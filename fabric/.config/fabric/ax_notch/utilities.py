"""
Utilities Panel - Power mode, Notes, Timer, Chronometer, DND, Night Light
"""

import subprocess
import json
import os
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.scrolledwindow import ScrolledWindow
from gi.repository import Gtk, GLib, Gdk
import datetime

from . import icons


class PowerModeSelector(Box):
    """Power mode/profile selector"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-power-mode",
            orientation="v",
            spacing=8,
            h_expand=True,
            **kwargs,
        )

        # Header
        header = Label(
            name="ax-power-mode-header",
            label="󰌪 Power Mode",
            h_align="start",
        )
        self.add(header)

        # Mode buttons
        modes_box = Box(
            name="ax-power-modes",
            orientation="h",
            spacing=8,
            homogeneous=True,
            h_expand=True,
        )

        self.modes = {
            "power-saver": ("󰾆", "Power Saver"),
            "balanced": ("󰾅", "Balanced"),
            "performance": ("󰓅", "Performance"),
        }

        self.mode_buttons = {}
        for mode_id, (icon, name) in self.modes.items():
            btn = Button(name=f"ax-power-mode-{mode_id}")
            content = Box(
                orientation="v",
                spacing=4,
                h_align="center",
                children=[
                    Label(name=f"ax-power-mode-{mode_id}-icon", label=icon),
                    Label(name=f"ax-power-mode-{mode_id}-name", label=name),
                ],
            )
            btn.add(content)
            btn.connect("clicked", self._on_mode_clicked, mode_id)
            modes_box.add(btn)
            self.mode_buttons[mode_id] = btn

        self.add(modes_box)

        # Update current mode
        GLib.idle_add(self._update_current_mode)

    def _get_current_mode(self):
        """Get current power profile"""
        try:
            result = subprocess.run(
                ["powerprofilesctl", "get"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except Exception:
            return "balanced"

    def _update_current_mode(self):
        """Update button states for current mode"""
        current = self._get_current_mode()
        for mode_id, btn in self.mode_buttons.items():
            if mode_id == current:
                btn.add_style_class("active")
            else:
                btn.remove_style_class("active")
        return False

    def _on_mode_clicked(self, btn, mode_id):
        """Set power mode"""
        try:
            subprocess.run(
                ["powerprofilesctl", "set", mode_id],
                timeout=5,
            )
            self._update_current_mode()
        except Exception:
            pass


class QuickNotes(Box):
    """Simple note-taking widget"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-notes",
            orientation="v",
            spacing=8,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )

        self.notes_file = os.path.expanduser("~/.local/share/ax-notch/notes.txt")
        os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)

        # Header
        header_box = Box(
            name="ax-notes-header",
            orientation="h",
            h_expand=True,
        )

        header = Label(
            name="ax-notes-title",
            label="󰎞 Quick Notes",
            h_align="start",
            h_expand=True,
        )

        clear_btn = Button(name="ax-notes-clear")
        clear_btn.add(Label(label="󰆴"))
        clear_btn.set_tooltip_text("Clear notes")
        clear_btn.connect("clicked", self._clear_notes)

        header_box.add(header)
        header_box.add(clear_btn)

        # Text view
        self.text_view = Gtk.TextView(name="ax-notes-text")
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_left_margin(8)
        self.text_view.set_right_margin(8)
        self.text_view.set_top_margin(8)
        self.text_view.set_bottom_margin(8)

        self.buffer = self.text_view.get_buffer()
        self.buffer.connect("changed", self._on_text_changed)

        scroll = ScrolledWindow(
            name="ax-notes-scroll",
            h_expand=True,
            v_expand=True,
        )
        scroll.set_min_content_height(80)
        scroll.add(self.text_view)

        self.add(header_box)
        self.add(scroll)

        # Load existing notes
        self._load_notes()

    def _load_notes(self):
        """Load notes from file"""
        try:
            if os.path.exists(self.notes_file):
                with open(self.notes_file, 'r') as f:
                    self.buffer.set_text(f.read())
        except Exception:
            pass

    def _save_notes(self):
        """Save notes to file"""
        try:
            start, end = self.buffer.get_bounds()
            text = self.buffer.get_text(start, end, True)
            with open(self.notes_file, 'w') as f:
                f.write(text)
        except Exception:
            pass

    def _on_text_changed(self, buffer):
        """Auto-save on change"""
        # Debounce saving
        if hasattr(self, '_save_timeout'):
            GLib.source_remove(self._save_timeout)
        self._save_timeout = GLib.timeout_add(1000, self._save_notes)

    def _clear_notes(self, btn):
        """Clear all notes"""
        self.buffer.set_text("")
        self._save_notes()


class Timer(Box):
    """Countdown timer widget"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-timer",
            orientation="v",
            spacing=8,
            h_expand=True,
            **kwargs,
        )

        self.remaining_seconds = 0
        self.is_running = False
        self.timer_id = None

        # Header
        header = Label(
            name="ax-timer-header",
            label="󰔛 Timer",
            h_align="start",
        )
        self.add(header)

        # Time display
        self.time_label = Label(
            name="ax-timer-display",
            label="00:00:00",
        )
        self.add(self.time_label)

        # Preset buttons
        presets_box = Box(
            name="ax-timer-presets",
            orientation="h",
            spacing=4,
            homogeneous=True,
            h_expand=True,
        )

        presets = [
            ("1m", 60),
            ("5m", 300),
            ("10m", 600),
            ("30m", 1800),
        ]

        for label, seconds in presets:
            btn = Button(name="ax-timer-preset")
            btn.add(Label(label=label))
            btn.connect("clicked", self._set_preset, seconds)
            presets_box.add(btn)

        self.add(presets_box)

        # Control buttons
        controls_box = Box(
            name="ax-timer-controls",
            orientation="h",
            spacing=8,
            h_align="center",
        )

        self.start_btn = Button(name="ax-timer-start")
        self.start_btn.add(Label(label=icons.play))
        self.start_btn.connect("clicked", self._toggle_timer)

        self.reset_btn = Button(name="ax-timer-reset")
        self.reset_btn.add(Label(label="󰑓"))
        self.reset_btn.connect("clicked", self._reset_timer)

        controls_box.add(self.start_btn)
        controls_box.add(self.reset_btn)

        self.add(controls_box)

    def _set_preset(self, btn, seconds):
        """Set timer to preset value"""
        self.remaining_seconds = seconds
        self._update_display()

    def _toggle_timer(self, btn):
        """Start/pause timer"""
        if self.is_running:
            self._pause_timer()
        else:
            self._start_timer()

    def _start_timer(self):
        """Start the timer"""
        if self.remaining_seconds <= 0:
            self.remaining_seconds = 60  # Default 1 minute
        self.is_running = True
        self.start_btn.get_child().set_label(icons.pause)
        self.start_btn.add_style_class("running")
        self.timer_id = GLib.timeout_add(1000, self._tick)

    def _pause_timer(self):
        """Pause the timer"""
        self.is_running = False
        self.start_btn.get_child().set_label(icons.play)
        self.start_btn.remove_style_class("running")
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

    def _reset_timer(self, btn):
        """Reset the timer"""
        self._pause_timer()
        self.remaining_seconds = 0
        self._update_display()

    def _tick(self):
        """Timer tick"""
        if not self.is_running:
            return False

        self.remaining_seconds -= 1
        self._update_display()

        if self.remaining_seconds <= 0:
            self._pause_timer()
            self._notify_complete()
            return False

        return True

    def _update_display(self):
        """Update time display"""
        hours = self.remaining_seconds // 3600
        minutes = (self.remaining_seconds % 3600) // 60
        seconds = self.remaining_seconds % 60
        self.time_label.set_label(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _notify_complete(self):
        """Send notification when timer completes"""
        try:
            subprocess.Popen(
                ["notify-send", "-u", "critical", "Timer", "Time's up!"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


class Stopwatch(Box):
    """Stopwatch/chronometer widget"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-stopwatch",
            orientation="v",
            spacing=8,
            h_expand=True,
            **kwargs,
        )

        self.elapsed_ms = 0
        self.is_running = False
        self.timer_id = None
        self.start_time = None

        # Header
        header = Label(
            name="ax-stopwatch-header",
            label="󱎫 Stopwatch",
            h_align="start",
        )
        self.add(header)

        # Time display
        self.time_label = Label(
            name="ax-stopwatch-display",
            label="00:00.000",
        )
        self.add(self.time_label)

        # Control buttons
        controls_box = Box(
            name="ax-stopwatch-controls",
            orientation="h",
            spacing=8,
            h_align="center",
        )

        self.start_btn = Button(name="ax-stopwatch-start")
        self.start_btn.add(Label(label=icons.play))
        self.start_btn.connect("clicked", self._toggle_stopwatch)

        self.reset_btn = Button(name="ax-stopwatch-reset")
        self.reset_btn.add(Label(label="󰑓"))
        self.reset_btn.connect("clicked", self._reset_stopwatch)

        controls_box.add(self.start_btn)
        controls_box.add(self.reset_btn)

        self.add(controls_box)

    def _toggle_stopwatch(self, btn):
        """Start/pause stopwatch"""
        if self.is_running:
            self._pause_stopwatch()
        else:
            self._start_stopwatch()

    def _start_stopwatch(self):
        """Start the stopwatch"""
        self.is_running = True
        self.start_time = GLib.get_monotonic_time() / 1000 - self.elapsed_ms
        self.start_btn.get_child().set_label(icons.pause)
        self.start_btn.add_style_class("running")
        self.timer_id = GLib.timeout_add(10, self._tick)

    def _pause_stopwatch(self):
        """Pause the stopwatch"""
        self.is_running = False
        self.start_btn.get_child().set_label(icons.play)
        self.start_btn.remove_style_class("running")
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

    def _reset_stopwatch(self, btn):
        """Reset the stopwatch"""
        self._pause_stopwatch()
        self.elapsed_ms = 0
        self._update_display()

    def _tick(self):
        """Stopwatch tick"""
        if not self.is_running:
            return False

        self.elapsed_ms = GLib.get_monotonic_time() / 1000 - self.start_time
        self._update_display()
        return True

    def _update_display(self):
        """Update time display"""
        total_ms = int(self.elapsed_ms)
        minutes = total_ms // 60000
        seconds = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        self.time_label.set_label(f"{minutes:02d}:{seconds:02d}.{ms:03d}")


class QuickToggle(Button):
    """Quick toggle button for DND, Night Light, etc."""

    def __init__(self, name: str, icon: str, label_text: str, is_active_fn, toggle_fn, **kwargs):
        super().__init__(
            name=f"ax-toggle-{name}",
            **kwargs,
        )

        self.is_active_fn = is_active_fn
        self.toggle_fn = toggle_fn

        content = Box(
            orientation="v",
            spacing=4,
            h_align="center",
            children=[
                Label(name=f"ax-toggle-{name}-icon", label=icon),
                Label(name=f"ax-toggle-{name}-label", label=label_text),
            ],
        )
        self.add(content)

        self.connect("clicked", self._on_clicked)
        GLib.idle_add(self._update_state)

    def _on_clicked(self, btn):
        """Toggle state"""
        self.toggle_fn()
        GLib.timeout_add(500, self._update_state)

    def _update_state(self):
        """Update button state"""
        if self.is_active_fn():
            self.add_style_class("active")
        else:
            self.remove_style_class("active")
        return False


class Utilities(Box):
    """Utilities panel with power mode, notes, timer, etc."""

    def __init__(self, notch=None, **kwargs):
        super().__init__(
            name="ax-utilities",
            orientation="v",
            spacing=16,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )

        self.notch = notch

        # Quick toggles row
        toggles_box = Box(
            name="ax-utilities-toggles",
            orientation="h",
            spacing=8,
            homogeneous=True,
            h_expand=True,
        )

        # Do Not Disturb toggle
        dnd_toggle = QuickToggle(
            name="dnd",
            icon="󰂛",
            label_text="DND",
            is_active_fn=self._is_dnd_active,
            toggle_fn=self._toggle_dnd,
        )

        # Night Light toggle
        night_toggle = QuickToggle(
            name="night",
            icon="󰖔",
            label_text="Night Light",
            is_active_fn=self._is_night_light_active,
            toggle_fn=self._toggle_night_light,
        )

        # Airplane mode toggle
        airplane_toggle = QuickToggle(
            name="airplane",
            icon="󰀝",
            label_text="Airplane",
            is_active_fn=self._is_airplane_active,
            toggle_fn=self._toggle_airplane,
        )

        # Screen recorder toggle
        record_toggle = QuickToggle(
            name="record",
            icon="󰑋",
            label_text="Record",
            is_active_fn=lambda: False,
            toggle_fn=self._start_recording,
        )

        toggles_box.add(dnd_toggle)
        toggles_box.add(night_toggle)
        toggles_box.add(airplane_toggle)
        toggles_box.add(record_toggle)

        # Power mode
        self.power_mode = PowerModeSelector()

        # Two-column layout for timer/stopwatch
        timers_box = Box(
            name="ax-utilities-timers",
            orientation="h",
            spacing=16,
            homogeneous=True,
            h_expand=True,
        )

        self.timer = Timer()
        self.stopwatch = Stopwatch()

        timers_box.add(self.timer)
        timers_box.add(self.stopwatch)

        # Notes (takes remaining space)
        self.notes = QuickNotes()

        self.add(toggles_box)
        self.add(self.power_mode)
        self.add(timers_box)
        self.add(self.notes)

    def _is_dnd_active(self):
        """Check if DND is active"""
        try:
            result = subprocess.run(
                ["dunstctl", "is-paused"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return result.stdout.strip() == "true"
        except Exception:
            return False

    def _toggle_dnd(self):
        """Toggle Do Not Disturb"""
        try:
            subprocess.run(["dunstctl", "set-paused", "toggle"], timeout=2)
        except Exception:
            pass

    def _is_night_light_active(self):
        """Check if night light is active"""
        try:
            # Try gammastep first
            result = subprocess.run(
                ["pgrep", "-x", "gammastep"],
                capture_output=True,
            )
            if result.returncode == 0:
                return True
            # Try redshift
            result = subprocess.run(
                ["pgrep", "-x", "redshift"],
                capture_output=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _toggle_night_light(self):
        """Toggle night light (gammastep/redshift)"""
        if self._is_night_light_active():
            # Kill running instance
            subprocess.run(["pkill", "-x", "gammastep"], capture_output=True)
            subprocess.run(["pkill", "-x", "redshift"], capture_output=True)
        else:
            # Start gammastep (or redshift as fallback)
            try:
                subprocess.Popen(
                    ["gammastep", "-O", "4500"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                try:
                    subprocess.Popen(
                        ["redshift", "-O", "4500"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass

    def _is_airplane_active(self):
        """Check if airplane mode is active"""
        try:
            result = subprocess.run(
                ["nmcli", "radio", "all"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Check if both wifi and wwan are disabled
            return "disabled" in result.stdout.lower()
        except Exception:
            return False

    def _toggle_airplane(self):
        """Toggle airplane mode"""
        try:
            if self._is_airplane_active():
                subprocess.run(["nmcli", "radio", "wifi", "on"], timeout=5)
                subprocess.run(["rfkill", "unblock", "all"], timeout=5)
            else:
                subprocess.run(["nmcli", "radio", "wifi", "off"], timeout=5)
                subprocess.run(["rfkill", "block", "all"], timeout=5)
        except Exception:
            pass

    def _start_recording(self):
        """Start/stop screen recording"""
        try:
            # Check if wf-recorder is running
            result = subprocess.run(
                ["pgrep", "-x", "wf-recorder"],
                capture_output=True,
            )
            if result.returncode == 0:
                # Stop recording
                subprocess.run(["pkill", "-x", "wf-recorder"])
            else:
                # Start recording
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.expanduser(f"~/Videos/recording_{timestamp}.mp4")
                subprocess.Popen(
                    ["wf-recorder", "-f", output_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass
