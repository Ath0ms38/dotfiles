"""
Homescreen Widgets — a full-screen desktop dashboard shown only when the
active workspace has no windows.

The window lives on the wlr-layer-shell "bottom" layer (above the wallpaper,
below every normal window), and is additionally hidden/shown from Hyprland
socket events so it disappears the instant a window opens.

Layout is a homogeneous 3x3 Gtk.Grid plus a quick-actions rail — cards can
never overlap and always fill the whole workarea. Cards use the same
frosted-glass look as kitty (theme background at 0.8 alpha; Hyprland blurs
the fabric layer namespace, ignore_alpha 0.50).

Weather comes from Open-Meteo (current conditions + 7-day forecast),
geolocated by IP or by the `homescreen_weather_location` config value.
"""

import json
import locale
import os
import shlex
import subprocess
import time
import urllib.parse
from collections import deque

import psutil
from fabric.hyprland.service import Hyprland
from fabric.utils import exec_shell_command_async
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.datetime import DateTime
from fabric.widgets.label import Label
from fabric.widgets.wayland import WaylandWindow
from gi.repository import GLib, Gtk

from services.config import get_config
from services.network import format_bandwidth

WEATHER_REFRESH_S = 30 * 60
UPDATES_REFRESH_S = 30 * 60
UI_TICK_S = 2
HISTORY_LEN = 120  # 4 minutes of history at 2s per sample

# Localized day abbreviations for the forecast row
try:
    locale.setlocale(locale.LC_TIME, "")
except locale.Error:
    pass


# --------------------------------------------------------------------------- #
# Data collection                                                             #
# --------------------------------------------------------------------------- #

class StatsCollector:
    """Always-on lightweight sampler feeding the graphs (2s /proc reads),
    so history is already filled when the homescreen appears."""

    _instance = None

    @classmethod
    def get(cls) -> "StatsCollector":
        if cls._instance is None:
            cls._instance = StatsCollector()
        return cls._instance

    def __init__(self):
        self.cpu = deque(maxlen=HISTORY_LEN)
        self.mem = deque(maxlen=HISTORY_LEN)
        self.rx = deque(maxlen=HISTORY_LEN)
        self.tx = deque(maxlen=HISTORY_LEN)

        self.cpu_pct = 0.0
        self.cpu_freq_ghz = 0.0
        self.cpu_temp = 0
        self.mem_used = 0
        self.mem_total = 1
        self.rx_speed = 0.0
        self.tx_speed = 0.0

        psutil.cpu_percent(interval=None)  # prime delta tracking
        counters = psutil.net_io_counters()
        self._last_net = (counters.bytes_recv, counters.bytes_sent, time.time())

        self._tick()
        GLib.timeout_add_seconds(UI_TICK_S, self._tick)

    def _tick(self):
        self.cpu_pct = psutil.cpu_percent(interval=None)
        self.cpu.append(self.cpu_pct / 100.0)

        freq = psutil.cpu_freq()
        self.cpu_freq_ghz = (freq.current / 1000.0) if freq else 0.0
        self.cpu_temp = self._read_temp()

        mem = psutil.virtual_memory()
        self.mem_used, self.mem_total = mem.used, mem.total
        self.mem.append(mem.percent / 100.0)

        counters = psutil.net_io_counters()
        last_rx, last_tx, last_t = self._last_net
        now = time.time()
        dt = max(now - last_t, 0.1)
        self.rx_speed = (counters.bytes_recv - last_rx) / dt
        self.tx_speed = (counters.bytes_sent - last_tx) / dt
        self._last_net = (counters.bytes_recv, counters.bytes_sent, now)

        self.rx.append(self.rx_speed)
        self.tx.append(self.tx_speed)

        return True

    @staticmethod
    def _read_temp() -> int:
        try:
            temps = psutil.sensors_temperatures()
            for chip in ("coretemp", "k10temp", "acpitz"):
                if chip in temps and temps[chip]:
                    return int(max(t.current for t in temps[chip]))
        except Exception:
            pass
        return 0


# --------------------------------------------------------------------------- #
# Building blocks                                                             #
# --------------------------------------------------------------------------- #

class Sparkline(Gtk.DrawingArea):
    """Filled line graph of a deque of samples; latest sample at the right
    edge. Stroke/fill color comes from the widget's CSS `color`. Expands to
    fill whatever space its card gives it."""

    def __init__(self, history: deque, normalize: bool = False):
        super().__init__(visible=True, hexpand=True, vexpand=True)
        self._history = history
        self._normalize = normalize
        self.set_size_request(180, 56)
        self.connect("draw", self._on_draw)

    def _on_draw(self, _widget, cr):
        alloc = self.get_allocation()
        w, h = alloc.width, alloc.height
        samples = list(self._history)
        if len(samples) < 2:
            return

        if self._normalize:
            ceiling = max(max(samples), 128 * 1024)  # ≥ 128 KiB/s
            samples = [s / ceiling for s in samples]

        color = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        step = w / (self._history.maxlen - 1)
        x0 = w - (len(samples) - 1) * step
        pad = 3

        def xy(i, v):
            return x0 + i * step, pad + (1.0 - min(max(v, 0.0), 1.0)) * (h - 2 * pad)

        cr.set_line_width(2)
        cr.set_source_rgba(color.red, color.green, color.blue, 0.95)
        cr.move_to(*xy(0, samples[0]))
        for i, v in enumerate(samples[1:], start=1):
            cr.line_to(*xy(i, v))
        cr.stroke_preserve()

        cr.line_to(x0 + (len(samples) - 1) * step, h)
        cr.line_to(x0, h)
        cr.close_path()
        cr.set_source_rgba(color.red, color.green, color.blue, 0.18)
        cr.fill()


class Card(Box):
    """A titled homescreen card (fills its grid cell)"""

    def __init__(self, title: str, icon: str, name: str, accent: str = "", **kwargs):
        super().__init__(
            name=name,
            style_classes=["homescreen-card"] + ([accent] if accent else []),
            orientation="v",
            spacing=8,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )
        self.title_label = Label(
            style_classes=["homescreen-card-title"],
            label=f"{icon}  {title}",
            h_align="start",
        )
        self.add(self.title_label)

    def tick(self):
        """Called every UI_TICK_S while the homescreen is visible"""


class GraphCard(Card):
    """Card with a big value, a detail line and an expanding sparkline"""

    def __init__(self, title, icon, name, history, accent, normalize=False, **kwargs):
        super().__init__(title, icon, name, accent=accent, **kwargs)

        top = Box(orientation="h", spacing=12)
        self.value = Label(style_classes=["homescreen-big"], label="…", h_align="start")
        self.detail = Label(
            style_classes=["homescreen-detail"],
            label="",
            h_align="end",
            v_align="end",
            h_expand=True,
        )
        top.add(self.value)
        top.add(self.detail)
        self.add(top)

        self.graph = Sparkline(history, normalize=normalize)
        self.graph.get_style_context().add_class("homescreen-graph")
        if accent:
            self.graph.get_style_context().add_class(accent)
        self.add(self.graph)

    def tick(self):
        self.graph.queue_draw()


class CpuCard(GraphCard):
    def __init__(self, stats: StatsCollector, **kwargs):
        super().__init__("CPU", "󰻠", "homescreen-cpu", stats.cpu,
                         accent="accent-a", **kwargs)
        self._stats = stats

    def tick(self):
        s = self._stats
        self.value.set_label(f"{s.cpu_pct:.0f}%")
        parts = [f"{s.cpu_freq_ghz:.1f} GHz"]
        if s.cpu_temp:
            parts.append(f"{s.cpu_temp}°C")
        parts.append(f"{psutil.cpu_count()} threads")
        self.detail.set_label("   ".join(parts))
        super().tick()


class RamCard(GraphCard):
    def __init__(self, stats: StatsCollector, **kwargs):
        super().__init__("Memory", "󰍛", "homescreen-ram", stats.mem,
                         accent="accent-b", **kwargs)
        self._stats = stats

    def tick(self):
        s = self._stats
        pct = 100.0 * s.mem_used / max(s.mem_total, 1)
        self.value.set_label(f"{pct:.0f}%")
        self.detail.set_label(
            f"{s.mem_used / 1024**3:.1f} / {s.mem_total / 1024**3:.0f} GiB"
        )
        super().tick()


class NetCard(Card):
    """Download + upload graphs stacked"""

    def __init__(self, stats: StatsCollector, **kwargs):
        super().__init__("Network", "󰛳", "homescreen-net", accent="accent-c", **kwargs)
        self._stats = stats

        self.down = Label(style_classes=["homescreen-detail", "accent-c"],
                          label="󰇚 …", h_align="start")
        self.up = Label(style_classes=["homescreen-detail", "accent-d"],
                        label="󰕒 …", h_align="end", h_expand=True)
        row = Box(orientation="h", spacing=12)
        row.add(self.down)
        row.add(self.up)
        self.add(row)

        self.rx_graph = Sparkline(stats.rx, normalize=True)
        self.rx_graph.get_style_context().add_class("homescreen-graph")
        self.rx_graph.get_style_context().add_class("accent-c")
        self.tx_graph = Sparkline(stats.tx, normalize=True)
        self.tx_graph.get_style_context().add_class("homescreen-graph")
        self.tx_graph.get_style_context().add_class("accent-d")
        self.add(self.rx_graph)
        self.add(self.tx_graph)

    def tick(self):
        self.down.set_label(f"󰇚 {format_bandwidth(self._stats.rx_speed)}")
        self.up.set_label(f"󰕒 {format_bandwidth(self._stats.tx_speed)}")
        self.rx_graph.queue_draw()
        self.tx_graph.queue_draw()


class GpuCard(GraphCard):
    """NVIDIA stats via nvidia-smi (async, every other tick)"""

    def __init__(self, **kwargs):
        self._history = deque(maxlen=HISTORY_LEN)
        super().__init__("GPU", "󰢮", "homescreen-gpu", self._history,
                         accent="accent-e", **kwargs)
        self.vram = Label(style_classes=["homescreen-detail"], label="",
                          h_align="start")
        # Put the VRAM line between the header row and the graph
        self.remove(self.graph)
        self.add(self.vram)
        self.add(self.graph)
        self._flip = False

    def tick(self):
        self._flip = not self._flip
        if self._flip:
            exec_shell_command_async(
                "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,"
                "temperature.gpu,power.draw,clocks.gr --format=csv,noheader,nounits",
                self._on_stats,
            )
        super().tick()

    def _on_stats(self, output):
        try:
            util, used, total, temp, power, clock = [
                float(x) for x in str(output).strip().split(",")
            ]
        except (ValueError, TypeError):
            return
        self._history.append(util / 100.0)
        self.value.set_label(f"{util:.0f}%")
        self.detail.set_label(f"{temp:.0f}°C   {power:.0f} W   {clock:.0f} MHz")
        self.vram.set_label(f"󰑭 VRAM  {used / 1024:.1f} / {total / 1024:.0f} GiB")
        self.graph.queue_draw()


class ProcsCard(Card):
    """Top processes by CPU; click to open btop"""

    ROWS = 7

    def __init__(self, **kwargs):
        super().__init__("Top processes", "󱕍", "homescreen-procs",
                         accent="accent-a", **kwargs)
        self._rows = []
        for _ in range(self.ROWS):
            row = Label(style_classes=["homescreen-mono"], label="", h_align="start")
            self._rows.append(row)
            self.add(row)
        self.add(Label(style_classes=["homescreen-hint"],
                       label="click to open btop", h_align="start",
                       v_expand=True, v_align="end"))

        # Prime psutil's per-process CPU delta tracking so the first visible
        # tick already has meaningful percentages
        for p in psutil.process_iter(["cpu_percent"]):
            pass

    def tick(self):
        procs = []
        for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            # Skip kernel threads (no memory of their own)
            if (info["memory_percent"] or 0) < 0.01:
                continue
            procs.append(info)
        procs.sort(key=lambda p: p["cpu_percent"] or 0, reverse=True)
        for row, p in zip(self._rows, procs[: self.ROWS]):
            name = (p["name"] or "?")[:22]
            row.set_label(
                f"{name:<23} {p['cpu_percent'] or 0:5.1f}%  {p['memory_percent'] or 0:4.1f}%"
            )

    @staticmethod
    def on_click(*_):
        subprocess.Popen(["kitty", "-e", "btop"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class DiskCard(Card):
    """Disk usage bars for real mounted partitions"""

    def __init__(self, **kwargs):
        super().__init__("Disks", "󰋊", "homescreen-disks", accent="accent-b", **kwargs)
        self._bars = {}

        seen_devices = set()
        for part in psutil.disk_partitions():
            if not part.device.startswith("/dev/") or part.device in seen_devices:
                continue
            seen_devices.add(part.device)

            header = Box(orientation="h", spacing=8)
            header.add(Label(style_classes=["homescreen-detail"],
                             label=part.mountpoint, h_align="start"))
            usage_label = Label(style_classes=["homescreen-detail"], label="",
                                h_align="end", h_expand=True)
            header.add(usage_label)

            bar = Gtk.LevelBar(min_value=0, max_value=100, visible=True,
                               hexpand=True)
            bar.get_style_context().add_class("homescreen-levelbar")
            self.add(header)
            self.add(bar)
            self._bars[part.mountpoint] = (bar, usage_label)

            if len(self._bars) >= 3:
                break

    def tick(self):
        for mount, (bar, label) in self._bars.items():
            try:
                usage = psutil.disk_usage(mount)
            except OSError:
                continue
            bar.set_value(usage.percent)
            label.set_label(
                f"{usage.used / 1024**3:.0f} / {usage.total / 1024**3:.0f} GiB"
                f"  ({usage.free / 1024**3:.0f} free)"
            )


class MediaCard(Card):
    """Now playing + controls (playerctl). Shown instead of Disks while
    something is playing."""

    def __init__(self, **kwargs):
        super().__init__("Now playing", "󰝚", "homescreen-media",
                         accent="accent-d", **kwargs)
        self.active = False

        self.track = Label(style_classes=["homescreen-media-title"], label="",
                           h_align="start", ellipsization="end")
        self.track.set_max_width_chars(30)
        self.artist = Label(style_classes=["homescreen-detail"], label="",
                            h_align="start", ellipsization="end")
        self.artist.set_max_width_chars(36)
        self.add(self.track)
        self.add(self.artist)

        controls = Box(orientation="h", spacing=8, h_align="center",
                       v_expand=True, v_align="end")
        for icon, action in (("󰒮", "previous"), ("󰐎", "play-pause"), ("󰒭", "next")):
            controls.add(Button(
                style_classes=["homescreen-media-btn"],
                label=icon,
                on_clicked=lambda _, a=action: self._ctl(a),
            ))
        self.add(controls)

    def _ctl(self, action):
        exec_shell_command_async(f"playerctl {action}", lambda *_: None)
        GLib.timeout_add(300, lambda: (self.tick(), False)[1])

    def tick(self):
        exec_shell_command_async(
            "playerctl metadata --format {{status}}|{{artist}}|{{title}}",
            self._on_metadata,
        )

    def _on_metadata(self, output):
        parts = str(output).strip().split("|")
        if len(parts) != 3 or parts[0] not in ("Playing", "Paused"):
            self.active = False
            return
        status, artist, title = parts
        self.active = True
        self.track.set_label(title or "Unknown")
        self.artist.set_label(f"{'' if status == 'Playing' else '󰏤 '}{artist}")


# WMO weather codes -> icon
def _wmo_icon(code: int) -> str:
    for codes, icon in (
        ((0,), "☀️"), ((1, 2), "🌤️"), ((3,), "☁️"), ((45, 48), "🌫️"),
        (tuple(range(51, 68)), "🌧️"), (tuple(range(71, 78)), "🌨️"),
        ((80, 81, 82), "🌦️"), ((85, 86), "🌨️"), ((95, 96, 99), "⛈️"),
    ):
        if code in codes:
            return icon
    return "🌡️"


class WeatherCard(Card):
    """Current conditions + 7-day forecast via Open-Meteo"""

    def __init__(self, **kwargs):
        super().__init__("Weather", "󰖐", "homescreen-weather",
                         accent="accent-b", **kwargs)
        self._last_fetch = 0.0
        self._coords = None
        self._place_name = ""

        top = Box(orientation="h", spacing=12)
        self.condition = Label(style_classes=["homescreen-big"], label="…",
                               h_align="start")
        self.location = Label(style_classes=["homescreen-hint"], label="",
                              h_align="end", v_align="end", h_expand=True)
        top.add(self.condition)
        top.add(self.location)
        self.add(top)

        self.details = Label(style_classes=["homescreen-detail"], label="",
                             h_align="start")
        self.add(self.details)

        # 7-day forecast row
        self._days = []
        week = Box(orientation="h", spacing=0, h_expand=True, v_expand=True,
                   v_align="end")
        for _ in range(7):
            col = Box(orientation="v", spacing=2, h_expand=True)
            name = Label(style_classes=["homescreen-day-name"], label="–")
            icon = Label(style_classes=["homescreen-day-icon"], label=" ")
            tmax = Label(style_classes=["homescreen-day-max"], label=" ")
            tmin = Label(style_classes=["homescreen-day-min"], label=" ")
            for widget in (name, icon, tmax, tmin):
                col.add(widget)
            week.add(col)
            self._days.append((name, icon, tmax, tmin))
        self.add(week)

    # -- fetch chain: coords (config name or IP) -> forecast ---------------

    def refresh_if_stale(self):
        if time.time() - self._last_fetch < WEATHER_REFRESH_S:
            return
        self._last_fetch = time.time()

        if self._coords:
            self._fetch_forecast()
            return

        place = get_config().homescreen_weather_location.strip()
        if place:
            query = urllib.parse.quote(place)
            exec_shell_command_async(
                'bash -c "curl -sf --max-time 10 '
                "'https://geocoding-api.open-meteo.com/v1/search"
                f"?name={query}&count=1&format=json'"
                ' | jq -c ."',
                self._on_geocode,
            )
        else:
            exec_shell_command_async(
                'bash -c "curl -sf --max-time 10 https://ipinfo.io/json | jq -c ."',
                self._on_iplocate,
            )

    def _on_geocode(self, output):
        try:
            result = json.loads(str(output))["results"][0]
            self._coords = (result["latitude"], result["longitude"])
            self._place_name = result.get("name", "")
        except (ValueError, KeyError, IndexError, TypeError):
            self._fail()
            return
        self._fetch_forecast()

    def _on_iplocate(self, output):
        try:
            info = json.loads(str(output))
            lat, lon = info["loc"].split(",")
            self._coords = (float(lat), float(lon))
            self._place_name = info.get("city", "")
        except (ValueError, KeyError, TypeError):
            self._fail()
            return
        self._fetch_forecast()

    def _fetch_forecast(self):
        lat, lon = self._coords
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            "weather_code,wind_speed_10m"
            "&daily=weather_code,temperature_2m_max,temperature_2m_min"
            "&timezone=auto&forecast_days=7"
        )
        exec_shell_command_async(
            f'bash -c "curl -sf --max-time 10 \'{url}\' | jq -c ."',
            self._on_forecast,
        )

    def _on_forecast(self, output):
        try:
            data = json.loads(str(output))
            current = data["current"]
            daily = data["daily"]
        except (ValueError, KeyError, TypeError):
            self._fail()
            return

        self.condition.set_label(
            f"{_wmo_icon(int(current['weather_code']))} "
            f"{current['temperature_2m']:.0f}°C"
        )
        self.details.set_label(
            f"Feels {current['apparent_temperature']:.0f}°C   "
            f"󰖝 {current['wind_speed_10m']:.0f} km/h   "
            f"󰖌 {current['relative_humidity_2m']:.0f}%"
        )
        if self._place_name:
            self.location.set_label(f"󰍎 {self._place_name}")

        for (name, icon, tmax, tmin), date, code, hi, lo in zip(
            self._days,
            daily["time"],
            daily["weather_code"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
        ):
            day = time.strftime("%a", time.strptime(date, "%Y-%m-%d"))
            name.set_label(day.rstrip(".").capitalize())
            icon.set_label(_wmo_icon(int(code)))
            tmax.set_label(f"{hi:.0f}°")
            tmin.set_label(f"{lo:.0f}°")

    def _fail(self):
        self.condition.set_label("unavailable")
        self._last_fetch = 0.0  # retry on next show


class CalendarCard(Card):
    def __init__(self, **kwargs):
        super().__init__("Calendar", "󰃭", "homescreen-calendar",
                         accent="accent-c", **kwargs)
        self.calendar = Gtk.Calendar(visible=True, hexpand=True, vexpand=True)
        self.calendar.set_property("show-details", False)
        self.add(self.calendar)

    def reset_to_today(self):
        now = time.localtime()
        self.calendar.select_month(now.tm_mon - 1, now.tm_year)
        self.calendar.select_day(now.tm_mday)


class ActionsColumn(Box):
    """Quick actions rail: lock, screenshot, clipboard, power"""

    ACTIONS = (
        ("󰌾", "Lock", "loginctl lock-session"),
        ("󰹑", "Screenshot", "hyprshot-gui"),
        ("󰅍", "Clipboard", "~/.config/rofi/scripts/clipboard.sh"),
        ("󰐥", "Power", "~/.config/rofi/scripts/power-menu.sh"),
    )

    def __init__(self, **kwargs):
        super().__init__(name="homescreen-actions", orientation="v",
                         spacing=12, v_align="center", **kwargs)
        for icon, tip, command in self.ACTIONS:
            self.add(Button(
                style_classes=["homescreen-action-btn"],
                label=icon,
                tooltip_text=tip,
                on_clicked=lambda _, c=command: subprocess.Popen(
                    shlex.split(os.path.expanduser(c)),
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                ),
            ))


class ClockCluster(Box):
    """Big clock + date + info chips (uptime, kernel, pacman updates)"""

    def __init__(self, **kwargs):
        super().__init__(name="homescreen-clock-box", orientation="v",
                         spacing=4, h_align="start", v_align="center", **kwargs)
        self._updates_fetch = 0.0

        # Click the clock to toggle seconds
        self.add(DateTime(formatters=["%H:%M", "%H:%M:%S"], interval=1000,
                          name="homescreen-clock", h_align="start"))
        self.add(DateTime(formatters=["%A %d %B"], interval=60000,
                          name="homescreen-date", h_align="start"))

        uname = os.uname()
        self.uptime_chip = self._chip("󰅐 …")
        self.updates_chip = self._chip("󰏖 …")
        chips = Box(orientation="h", spacing=8, h_align="start",
                    style_classes=["homescreen-chips"])
        chips.add(self.uptime_chip)
        chips.add(self._chip(f"󰌽 {uname.release.split('-')[0]}"))
        chips.add(self.updates_chip)
        self.add(chips)

    @staticmethod
    def _chip(text):
        return Label(style_classes=["homescreen-chip"], label=text)

    def tick(self):
        try:
            with open("/proc/uptime") as f:
                seconds = float(f.read().split()[0])
            hours, minutes = int(seconds // 3600), int(seconds % 3600 // 60)
            label = f"󰅐 {hours}h {minutes:02d}m" if hours else f"󰅐 {minutes}m"
            self.uptime_chip.set_label(label)
        except OSError:
            pass

    def refresh_updates_if_stale(self):
        if time.time() - self._updates_fetch < UPDATES_REFRESH_S:
            return
        if not GLib.find_program_in_path("checkupdates"):
            self.updates_chip.hide()
            return
        self._updates_fetch = time.time()
        exec_shell_command_async(
            'bash -c "checkupdates 2>/dev/null | wc -l"',
            lambda out: self.updates_chip.set_label(
                f"󰏖 {str(out).strip() or 0} updates"),
        )


# --------------------------------------------------------------------------- #
# The window                                                                  #
# --------------------------------------------------------------------------- #

SLIDE = Gtk.RevealerTransitionType


class Homescreen(WaylandWindow):
    """Per-monitor full-screen desktop dashboard (bottom layer).

    Homogeneous 3x3 grid + actions rail: cards can never overlap and always
    fill the workarea.
    """

    def __init__(self, monitor: int, workarea: tuple[int, int], **kwargs):
        super().__init__(
            layer="bottom",
            anchor="top left right bottom",
            exclusivity="none",
            keyboard_mode="none",
            monitor=monitor,
            name="homescreen",
            visible=False,
            all_visible=False,
            **kwargs,
        )
        stats = StatsCollector.get()
        self._tick_id = None
        self._revealers = []

        self.set_size_request(*workarea)

        self.clock = ClockCluster()
        self.weather = WeatherCard()
        self.calendar = CalendarCard()
        self.media = MediaCard()
        self.disks = DiskCard()
        self.cpu = CpuCard(stats)
        self.ram = RamCard(stats)
        self.net = NetCard(stats)
        self.gpu = GpuCard() if GLib.find_program_in_path("nvidia-smi") else None
        procs = ProcsCard()

        procs_clickable = Gtk.EventBox(visible=True, hexpand=True, vexpand=True)
        procs_clickable.add(procs)
        procs_clickable.connect("button-press-event", procs.on_click)

        # Disks card swaps to the media player while something is playing
        self._stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.CROSSFADE,
            transition_duration=400,
            visible=True, hexpand=True, vexpand=True,
        )
        self._stack.add_named(self.disks, "disks")
        self._stack.add_named(self.media, "media")

        self._tickables = [c for c in (
            self.clock, self.cpu, self.ram, self.net, self.gpu, procs,
            self.media, self.disks,
        ) if c is not None]

        grid = Gtk.Grid(
            visible=True,
            hexpand=True, vexpand=True,
            row_homogeneous=True, column_homogeneous=True,
            row_spacing=24, column_spacing=24,
        )

        # Row 0: identity + compute
        self._cell(grid, self.clock, 0, 0, SLIDE.CROSSFADE)
        self._cell(grid, self.cpu, 1, 0, SLIDE.SLIDE_DOWN)
        self._cell(grid, self.gpu or Box(), 2, 0, SLIDE.SLIDE_DOWN)
        # Row 1: calendar + memory + weather
        self._cell(grid, self.calendar, 0, 1, SLIDE.SLIDE_RIGHT)
        self._cell(grid, self.ram, 1, 1, SLIDE.CROSSFADE)
        self._cell(grid, self.weather, 2, 1, SLIDE.SLIDE_LEFT)
        # Row 2: activity
        self._cell(grid, procs_clickable, 0, 2, SLIDE.SLIDE_UP)
        self._cell(grid, self.net, 1, 2, SLIDE.SLIDE_UP)
        self._cell(grid, self._stack, 2, 2, SLIDE.SLIDE_UP)

        root = Box(orientation="h", spacing=24, h_expand=True, v_expand=True)
        for side in ("top", "bottom", "start", "end"):
            getattr(root, f"set_margin_{side}")(32)
        root.add(grid)
        root.add(ActionsColumn())
        self.add(root)

        self.connect("map", self._on_map)
        self.connect("unmap", self._on_unmap)

    def _cell(self, grid, widget, col, row, transition):
        revealer = Gtk.Revealer(
            transition_type=transition,
            transition_duration=450,
            visible=True, hexpand=True, vexpand=True,
        )
        revealer.add(widget)
        grid.attach(revealer, col, row, 1, 1)
        self._revealers.append(revealer)

    # -- visibility ---------------------------------------------------------

    def show_widgets(self):
        if self.get_visible():
            return
        for revealer in self._revealers:
            revealer.set_reveal_child(False)
        self.calendar.reset_to_today()
        # Pick the disks/media pane instantly — only animate changes that
        # happen while visible
        self._stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self._stack.set_visible_child_name("media" if self.media.active else "disks")
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.show_all()

        for i, revealer in enumerate(self._revealers):
            GLib.timeout_add(60 + i * 60,
                             lambda r=revealer: r.set_reveal_child(True) or False)

        self.weather.refresh_if_stale()
        self.clock.refresh_updates_if_stale()

    def hide_widgets(self):
        # Instant — no exit animation, a window is taking over the screen
        self.hide()

    def _on_map(self, *_):
        self._tick()
        if self._tick_id is None:
            self._tick_id = GLib.timeout_add_seconds(UI_TICK_S, self._tick)

    def _on_unmap(self, *_):
        if self._tick_id is not None:
            GLib.source_remove(self._tick_id)
            self._tick_id = None

    def _tick(self):
        for card in self._tickables:
            card.tick()
        self._stack.set_visible_child_name("media" if self.media.active else "disks")
        return True


# --------------------------------------------------------------------------- #
# Visibility manager                                                          #
# --------------------------------------------------------------------------- #

class HomescreenManager:
    """Shows/hides the per-monitor homescreens from Hyprland socket events"""

    def __init__(self, windows: dict[int, Homescreen]):
        self._windows = windows
        self._sync_queued = False
        self.windows = list(windows.values())

        self._hyprland = Hyprland()
        for event in (
            "event::openwindow",
            "event::closewindow",
            "event::movewindow",
            "event::workspace",
            "event::focusedmon",
            "event::monitoradded",
            "event::monitorremoved",
        ):
            self._hyprland.connect(event, self._on_event)

        GLib.idle_add(self._sync)

    def _on_event(self, *_):
        # Coalesce event bursts into a single sync per main-loop iteration
        if self._sync_queued:
            return
        self._sync_queued = True
        GLib.idle_add(self._sync)

    @staticmethod
    def _hyprctl_json(command: str):
        try:
            result = Hyprland.send_command(f"j/{command}")
            if result and result.reply:
                return json.loads(result.reply)
        except Exception:
            pass
        try:
            output = subprocess.check_output(["hyprctl", command, "-j"], text=True)
            return json.loads(output)
        except Exception:
            return []

    def _sync(self):
        self._sync_queued = False
        monitors = self._hyprctl_json("monitors")
        clients = self._hyprctl_json("clients")

        windows_per_workspace: dict[int, int] = {}
        for client in clients:
            if not client.get("mapped", True):
                continue
            ws = client.get("workspace", {}).get("id")
            if ws is not None:
                windows_per_workspace[ws] = windows_per_workspace.get(ws, 0) + 1

        for mon in monitors:
            homescreen = self._windows.get(mon.get("id"))
            if homescreen is None:
                continue

            active_ws = mon.get("activeWorkspace", {}).get("id")
            occupied = windows_per_workspace.get(active_ws, 0) > 0
            # An overlaid special workspace (scratchpad) also counts as occupied
            if mon.get("specialWorkspace", {}).get("id"):
                occupied = True

            if occupied:
                homescreen.hide_widgets()
            else:
                homescreen.show_widgets()

        return False


def create_homescreens(monitors) -> HomescreenManager | None:
    """Create one homescreen per monitor and the manager driving them"""
    if not get_config().homescreen_enabled:
        return None

    workareas = {}
    for mon in HomescreenManager._hyprctl_json("monitors"):
        scale = mon.get("scale", 1.0) or 1.0
        left, top, right, bottom = mon.get("reserved", [0, 0, 0, 0])
        workareas[mon["id"]] = (
            int(mon["width"] / scale) - left - right,
            int(mon["height"] / scale) - top - bottom,
        )

    windows = {
        m.id: Homescreen(monitor=m.id, workarea=workareas.get(m.id, (1920, 1030)))
        for m in monitors
    }
    if not windows:
        return None
    return HomescreenManager(windows)
