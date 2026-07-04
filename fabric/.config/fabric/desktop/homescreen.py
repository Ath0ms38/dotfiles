"""
Homescreen Widgets — a full-screen desktop dashboard shown only when the
active workspace has no windows.

The window lives on the wlr-layer-shell "bottom" layer (above the wallpaper,
below every normal window), and is additionally hidden/shown from Hyprland
socket events so it disappears the instant a window opens.

Cards are scattered across the whole screen (Gtk.Fixed, fraction-based
positions), each with its own entrance animation. Live Cairo sparkline
graphs for CPU / RAM / network / GPU, top processes, media controls,
weather, calendar and quick actions.
"""

import json
import os
import shlex
import subprocess
import time
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

WEATHER_URL = "https://wttr.in/{location}?format=%l|%c|%t|%f|%w|%h|%S|%s|%p"
WEATHER_REFRESH_S = 30 * 60
UPDATES_REFRESH_S = 30 * 60
UI_TICK_S = 2
HISTORY_LEN = 120  # 4 minutes of history at 2s per sample


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

        # Normalize network history against a rolling ceiling (min 1 MiB/s)
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
    edge. Stroke/fill color comes from the widget's CSS `color`."""

    def __init__(self, history: deque, width: int = 320, height: int = 100,
                 normalize: bool = False):
        super().__init__(visible=True)
        self._history = history
        self._normalize = normalize
        self.set_size_request(width, height)
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

        # Fill under the curve
        cr.line_to(x0 + (len(samples) - 1) * step, h)
        cr.line_to(x0, h)
        cr.close_path()
        cr.set_source_rgba(color.red, color.green, color.blue, 0.18)
        cr.fill()


class Card(Box):
    """A titled homescreen card"""

    def __init__(self, title: str, icon: str, name: str, accent: str = "", **kwargs):
        super().__init__(
            name=name,
            style_classes=["homescreen-card"] + ([accent] if accent else []),
            orientation="v",
            spacing=8,
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
    """Card with a big value, a detail line and a sparkline"""

    def __init__(self, title, icon, name, history, accent, width=320,
                 normalize=False, **kwargs):
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

        self.graph = Sparkline(history, width=width, normalize=normalize)
        self.graph.get_style_context().add_class("homescreen-graph")
        if accent:
            self.graph.get_style_context().add_class(accent)
        self.add(self.graph)

    def tick(self):
        self.graph.queue_draw()


class CpuCard(GraphCard):
    def __init__(self, stats: StatsCollector, **kwargs):
        super().__init__("CPU", "󰻠", "homescreen-cpu", stats.cpu,
                         accent="accent-a", width=560, **kwargs)
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
                         accent="accent-b", width=520, **kwargs)
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

        self.rx_graph = Sparkline(stats.rx, width=520, height=68, normalize=True)
        self.rx_graph.get_style_context().add_class("homescreen-graph")
        self.rx_graph.get_style_context().add_class("accent-c")
        self.tx_graph = Sparkline(stats.tx, width=520, height=46, normalize=True)
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
                         accent="accent-e", width=300, **kwargs)
        self._flip = False

    def tick(self):
        self._flip = not self._flip
        if self._flip:
            exec_shell_command_async(
                "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,"
                "temperature.gpu --format=csv,noheader,nounits",
                self._on_stats,
            )
        super().tick()

    def _on_stats(self, output):
        try:
            util, used, total, temp = [int(x) for x in str(output).strip().split(",")]
        except (ValueError, TypeError):
            return
        self._history.append(util / 100.0)
        self.value.set_label(f"{util}%")
        self.detail.set_label(f"{used / 1024:.1f} / {total / 1024:.0f} GiB   {temp}°C")
        self.graph.queue_draw()


class ProcsCard(Card):
    """Top processes by CPU; click to open btop"""

    ROWS = 8

    def __init__(self, **kwargs):
        super().__init__("Top processes", "󱕍", "homescreen-procs",
                         accent="accent-a", **kwargs)
        self._rows = []
        for _ in range(self.ROWS):
            row = Label(style_classes=["homescreen-mono"], label="", h_align="start")
            self._rows.append(row)
            self.add(row)
        self.add(Label(style_classes=["homescreen-hint"],
                       label="click to open btop", h_align="start"))

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


class MediaCard(Card):
    """Now playing + controls (playerctl). Revealed only while playing."""

    def __init__(self, **kwargs):
        super().__init__("Now playing", "󰝚", "homescreen-media",
                         accent="accent-d", **kwargs)
        self.active = False

        self.track = Label(style_classes=["homescreen-media-title"], label="",
                           h_align="start", ellipsization="end")
        self.track.set_max_width_chars(32)
        self.artist = Label(style_classes=["homescreen-detail"], label="",
                            h_align="start", ellipsization="end")
        self.artist.set_max_width_chars(36)
        self.add(self.track)
        self.add(self.artist)

        controls = Box(orientation="h", spacing=8, h_align="center")
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


class WeatherCard(Card):
    def __init__(self, **kwargs):
        super().__init__("Weather", "󰖐", "homescreen-weather",
                         accent="accent-b", **kwargs)
        self._last_fetch = 0.0

        self.condition = Label(style_classes=["homescreen-big"], label="…",
                               h_align="start")
        self.details = Label(style_classes=["homescreen-detail"], label="",
                             h_align="start")
        self.sun = Label(style_classes=["homescreen-detail"], label="",
                         h_align="start")
        self.location = Label(style_classes=["homescreen-hint"], label="",
                              h_align="start")
        for w in (self.condition, self.details, self.sun, self.location):
            self.add(w)

    def refresh_if_stale(self):
        if time.time() - self._last_fetch < WEATHER_REFRESH_S:
            return
        self._last_fetch = time.time()
        location = get_config().homescreen_weather_location
        exec_shell_command_async(
            f"curl -sf --max-time 10 '{WEATHER_URL.format(location=location)}'",
            self._on_weather,
        )

    def _on_weather(self, output):
        parts = [p.strip() for p in str(output).strip().split("|")]
        if len(parts) != 9 or not parts[2]:
            self.condition.set_label("unavailable")
            self._last_fetch = 0.0
            return
        location, condition, temp, feels, wind, humidity, sunrise, sunset, precip = parts
        self.condition.set_label(f"{condition}  {temp}")
        self.details.set_label(f"Feels {feels}   󰖝 {wind}   󰖌 {humidity}   󰖗 {precip}")
        self.sun.set_label(f"󰖜 {sunrise[:5]}    󰖛 {sunset[:5]}")
        # IP geolocation returns raw "lat,lon" — only show real place names
        self.location.set_label(
            f"󰍎 {location}" if any(ch.isalpha() for ch in location) else ""
        )


class CalendarCard(Card):
    def __init__(self, **kwargs):
        super().__init__("Calendar", "󰃭", "homescreen-calendar",
                         accent="accent-c", **kwargs)
        self.calendar = Gtk.Calendar(visible=True)
        self.calendar.set_property("show-details", False)
        self.add(self.calendar)

    def reset_to_today(self):
        now = time.localtime()
        self.calendar.select_month(now.tm_mon - 1, now.tm_year)
        self.calendar.select_day(now.tm_mday)


class ActionsColumn(Box):
    """Quick actions: lock, screenshot, clipboard, power"""

    ACTIONS = (
        ("󰌾", "Lock", "loginctl lock-session"),
        ("󰹑", "Screenshot", "hyprshot-gui"),
        ("󰅍", "Clipboard", "~/.config/rofi/scripts/clipboard.sh"),
        ("󰐥", "Power", "~/.config/rofi/scripts/power-menu.sh"),
    )

    def __init__(self, **kwargs):
        super().__init__(name="homescreen-actions", orientation="v",
                         spacing=12, **kwargs)
        for icon, tip, command in self.ACTIONS:
            btn = Button(
                style_classes=["homescreen-action-btn"],
                label=icon,
                tooltip_text=tip,
                on_clicked=lambda _, c=command: subprocess.Popen(
                    shlex.split(os.path.expanduser(c)),
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                ),
            )
            self.add(btn)


class ClockCluster(Box):
    """Big clock + date + info chips (uptime, kernel, pacman updates)"""

    def __init__(self, **kwargs):
        super().__init__(name="homescreen-clock-box", orientation="v",
                         spacing=4, **kwargs)
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

# (x, y) as fractions of the workarea; transition; size request width or None
SLIDE = Gtk.RevealerTransitionType


class Homescreen(WaylandWindow):
    """Per-monitor full-screen desktop dashboard (bottom layer)"""

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
        # Fixed pixel geometry from hyprctl — placing by window allocation is
        # racy: the layer surface starts content-sized and grows to full
        # screen over several configures
        self._workarea = workarea
        self._placements = []

        self._fixed = Gtk.Fixed(visible=True)
        self.set_size_request(*workarea)
        self.add(self._fixed)

        self.clock = ClockCluster()
        self.weather = WeatherCard()
        self.calendar = CalendarCard()
        self.media = MediaCard()
        self.cpu = CpuCard(stats)
        self.ram = RamCard(stats)
        self.net = NetCard(stats)
        self.gpu = GpuCard() if GLib.find_program_in_path("nvidia-smi") else None
        procs = ProcsCard()

        procs_clickable = Gtk.EventBox(visible=True)
        procs_clickable.add(procs)
        procs_clickable.connect("button-press-event", procs.on_click)

        self._tickables = [c for c in (
            self.clock, self.cpu, self.ram, self.net, self.gpu, procs, self.media,
        ) if c is not None]

        # The scattered layout ("a little disorganized" by design)
        self._place(self.clock, 0.040, 0.050, SLIDE.SLIDE_RIGHT)
        self._place(self.calendar, 0.045, 0.400, SLIDE.SLIDE_RIGHT)
        self._place(procs_clickable, 0.040, 0.725, SLIDE.SLIDE_RIGHT)
        self._place(self.cpu, 0.280, 0.095, SLIDE.SLIDE_DOWN)
        self._place(self.ram, 0.300, 0.420, SLIDE.SLIDE_UP)
        self._place(self.net, 0.275, 0.720, SLIDE.SLIDE_UP)
        self._place(self.weather, 0.640, 0.070, SLIDE.SLIDE_LEFT)
        self._place(self.gpu, 0.625, 0.380, SLIDE.SLIDE_DOWN)
        self.media_revealer = self._place(self.media, 0.655, 0.720, SLIDE.SLIDE_UP)
        self._place(ActionsColumn(), 0.952, 0.300, SLIDE.SLIDE_LEFT)

        self.connect("map", self._on_map)
        self.connect("unmap", self._on_unmap)

    def _place(self, widget, xf, yf, transition):
        if widget is None:
            return None
        revealer = Gtk.Revealer(
            transition_type=transition,
            transition_duration=500,
            visible=True,
        )
        revealer.add(widget)
        w, h = self._workarea
        self._fixed.put(revealer, int(xf * w), int(yf * h))
        self._placements.append((revealer, xf, yf))
        return revealer

    # -- visibility ---------------------------------------------------------

    def show_widgets(self):
        if self.get_visible():
            return
        for revealer, *_ in self._placements:
            revealer.set_reveal_child(False)
        self.calendar.reset_to_today()
        self.show_all()

        # Staggered entrance, each card sliding from its own direction
        for i, (revealer, *_ ) in enumerate(self._placements):
            if revealer is self.media_revealer:
                continue  # revealed by the media poll only while playing
            GLib.timeout_add(60 + i * 70,
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
        if self.media_revealer:
            self.media_revealer.set_reveal_child(self.media.active)
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
