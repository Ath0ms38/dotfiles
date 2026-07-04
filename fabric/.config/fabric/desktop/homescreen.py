"""
Homescreen Widgets — a desktop layer shown only when the active workspace
has no windows.

The window lives on the wlr-layer-shell "bottom" layer (above the wallpaper,
below every normal window), and is additionally hidden/shown from Hyprland
socket events so it disappears the instant a window opens.

Widgets: big clock, calendar, weather (wttr.in), system info.
"""

import json
import os
import subprocess
import time

import psutil
from fabric.hyprland.service import Hyprland
from fabric.utils import exec_shell_command_async
from fabric.widgets.box import Box
from fabric.widgets.datetime import DateTime
from fabric.widgets.label import Label
from fabric.widgets.wayland import WaylandWindow
from gi.repository import GLib, Gtk

from services.config import get_config

# wttr.in one-liner: location | condition | temp | feels-like | wind | humidity
WEATHER_URL = "https://wttr.in/{location}?format=%l|%c|%t|%f|%w|%h"
WEATHER_REFRESH_S = 30 * 60
SYSINFO_REFRESH_S = 3


class Card(Box):
    """A titled homescreen card"""

    def __init__(self, title: str, icon: str, name: str, **kwargs):
        super().__init__(
            name=name,
            style_classes=["homescreen-card"],
            orientation="v",
            spacing=8,
            **kwargs,
        )
        self.add(
            Label(
                style_classes=["homescreen-card-title"],
                label=f"{icon}  {title}",
                h_align="start",
            )
        )


class WeatherCard(Card):
    """Current weather from wttr.in (refreshed every 30 min while shown)"""

    def __init__(self, **kwargs):
        super().__init__("Weather", "󰖐", "homescreen-weather", **kwargs)
        self._last_fetch = 0.0

        self.condition = Label(
            style_classes=["homescreen-weather-main"], label="…", h_align="start"
        )
        self.details = Label(
            style_classes=["homescreen-weather-details"], label="", h_align="start"
        )
        self.location = Label(
            style_classes=["homescreen-weather-location"], label="", h_align="start"
        )
        for w in (self.condition, self.details, self.location):
            self.add(w)

    def refresh_if_stale(self):
        if time.time() - self._last_fetch < WEATHER_REFRESH_S:
            return
        self._last_fetch = time.time()
        location = get_config().homescreen_weather_location
        url = WEATHER_URL.format(location=location)
        exec_shell_command_async(
            f"curl -sf --max-time 10 '{url}'", self._on_weather
        )

    def _on_weather(self, output):
        parts = [p.strip() for p in str(output).strip().split("|")]
        if len(parts) != 6 or not parts[2]:
            self.condition.set_label("Weather unavailable")
            self.details.set_label("")
            # Retry on next show
            self._last_fetch = 0.0
            return
        location, condition, temp, feels, wind, humidity = parts
        self.condition.set_label(f"{condition}  {temp}")
        self.details.set_label(f"Feels {feels}   󰖝 {wind}   󰖌 {humidity}")
        # IP geolocation returns raw "lat,lon" — only show real place names
        if any(ch.isalpha() for ch in location):
            self.location.set_label(f"󰍎 {location}")
        else:
            self.location.set_label("")


class SystemCard(Card):
    """Host info + live CPU/RAM/disk/uptime (updates only while shown)"""

    def __init__(self, **kwargs):
        super().__init__("System", "󰍛", "homescreen-system", **kwargs)
        self._timer_id = None

        uname = os.uname()
        self.add(
            Label(
                style_classes=["homescreen-system-host"],
                label=f"{uname.nodename}  ·  {uname.release}",
                h_align="start",
            )
        )

        self.cpu = self._row("󰻠", "CPU")
        self.mem = self._row("󰍛", "RAM")
        self.disk = self._row("󰋊", "Disk")
        self.uptime = self._row("󰅐", "Up")

        # Prime psutil's cpu_percent delta tracking
        psutil.cpu_percent(interval=None)

        self.connect("map", self._on_map)
        self.connect("unmap", self._on_unmap)

    def _row(self, icon: str, title: str) -> Label:
        row = Box(orientation="h", spacing=8)
        row.add(Label(style_classes=["homescreen-system-icon"], label=icon))
        row.add(Label(style_classes=["homescreen-system-key"], label=title, h_align="start"))
        value = Label(
            style_classes=["homescreen-system-value"],
            label="…",
            h_align="end",
            h_expand=True,
        )
        row.add(value)
        self.add(row)
        return value

    def _on_map(self, *_):
        self._update()
        if self._timer_id is None:
            self._timer_id = GLib.timeout_add_seconds(SYSINFO_REFRESH_S, self._update)

    def _on_unmap(self, *_):
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _update(self):
        self.cpu.set_label(f"{psutil.cpu_percent(interval=None):.0f}%")

        mem = psutil.virtual_memory()
        self.mem.set_label(
            f"{mem.used / 1024**3:.1f} / {mem.total / 1024**3:.0f} GiB"
        )

        disk = psutil.disk_usage("/")
        self.disk.set_label(f"{disk.percent:.0f}%  ({disk.free / 1024**3:.0f} GiB free)")

        try:
            with open("/proc/uptime") as f:
                seconds = float(f.read().split()[0])
            hours, minutes = int(seconds // 3600), int(seconds % 3600 // 60)
            self.uptime.set_label(f"{hours}h {minutes:02d}m" if hours else f"{minutes}m")
        except OSError:
            pass

        return True


class CalendarCard(Card):
    """Monthly calendar"""

    def __init__(self, **kwargs):
        super().__init__("Calendar", "󰃭", "homescreen-calendar", **kwargs)
        self.calendar = Gtk.Calendar(visible=True)
        self.calendar.set_property("show-details", False)
        self.add(self.calendar)

    def reset_to_today(self):
        now = time.localtime()
        self.calendar.select_month(now.tm_mon - 1, now.tm_year)
        self.calendar.select_day(now.tm_mday)


class Homescreen(WaylandWindow):
    """Per-monitor desktop widget layer (bottom layer, below all windows)"""

    def __init__(self, monitor: int, **kwargs):
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

        self.weather = WeatherCard()
        self.calendar = CalendarCard()
        self.system = SystemCard()

        clock_box = Box(
            name="homescreen-clock-box",
            orientation="v",
            spacing=0,
            h_align="center",
            children=[
                DateTime(formatters=["%H:%M"], interval=1000, name="homescreen-clock"),
                DateTime(formatters=["%A %d %B"], interval=60000, name="homescreen-date"),
            ],
        )

        cards_box = Box(
            name="homescreen-cards",
            orientation="h",
            spacing=24,
            h_align="center",
            children=[self.calendar, self.weather, self.system],
        )

        # Revealers give the entrance animation (staggered on show)
        self.clock_revealer = Gtk.Revealer(
            transition_type=Gtk.RevealerTransitionType.CROSSFADE,
            transition_duration=500,
        )
        self.clock_revealer.add(clock_box)

        self.cards_revealer = Gtk.Revealer(
            transition_type=Gtk.RevealerTransitionType.SLIDE_UP,
            transition_duration=450,
        )
        self.cards_revealer.add(cards_box)

        content = Box(
            name="homescreen-content",
            orientation="v",
            spacing=48,
            v_align="center",
            h_align="center",
            v_expand=True,
            h_expand=True,
        )
        content.add(self.clock_revealer)
        content.add(self.cards_revealer)
        self.add(content)

    def show_widgets(self):
        if self.get_visible():
            return
        # Start collapsed so the reveal animates every time
        self.clock_revealer.set_reveal_child(False)
        self.cards_revealer.set_reveal_child(False)
        self.calendar.reset_to_today()
        self.show_all()
        # Staggered entrance
        GLib.timeout_add(30, lambda: self.clock_revealer.set_reveal_child(True) or False)
        GLib.timeout_add(180, lambda: self.cards_revealer.set_reveal_child(True) or False)
        self.weather.refresh_if_stale()

    def hide_widgets(self):
        # Instant — no exit animation, a window is taking over the screen
        self.hide()


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

    windows = {m.id: Homescreen(monitor=m.id) for m in monitors}
    if not windows:
        return None
    return HomescreenManager(windows)
