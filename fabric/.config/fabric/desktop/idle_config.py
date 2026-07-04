"""
Idle timing configuration — a popover on the homescreen actions rail that
edits ~/.config/hypr/hypridle.conf (enable/disable + minutes for screen-off,
lock and suspend) and restarts hypridle.

The file is edited in place: only comment markers and timeout values of the
three managed listener blocks are touched, everything else (general block,
brightness-dim listener, user comments) is preserved verbatim.
"""

import os
import re
import subprocess

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from gi.repository import Gtk

HYPRIDLE_CONF = os.path.expanduser("~/.config/hypr/hypridle.conf")

# kind -> substring identifying its listener block's on-timeout command
MANAGED = {
    "lock": "loginctl lock-session",
    "dpms": "dpms off",
    "suspend": "systemctl suspend",
}


def _find_blocks(lines):
    """Yield (start, end, kind) line ranges of managed listener blocks
    (commented or not)."""
    start = None
    for i, line in enumerate(lines):
        stripped = re.sub(r"^\s*#\s?", "", line).strip()
        if start is None:
            if re.match(r"listener\s*{", stripped):
                start = i
        else:
            if stripped.startswith("}"):
                body = "\n".join(
                    re.sub(r"^\s*#\s?", "", l) for l in lines[start:i + 1]
                )
                for kind, key in MANAGED.items():
                    if key in body:
                        yield start, i, kind
                        break
                start = None


def read_settings():
    """Return {kind: (enabled, seconds)} parsed from hypridle.conf"""
    settings = {kind: (False, default) for kind, default in
                (("lock", 300), ("dpms", 330), ("suspend", 1800))}
    try:
        lines = open(HYPRIDLE_CONF).read().splitlines()
    except OSError:
        return settings

    for start, end, kind in _find_blocks(lines):
        enabled = not lines[start].lstrip().startswith("#")
        seconds = settings[kind][1]
        for line in lines[start:end + 1]:
            match = re.search(r"timeout\s*=\s*(\d+)", line)
            if match:
                seconds = int(match.group(1))
                break
        settings[kind] = (enabled, seconds)
    return settings


def write_settings(settings):
    """Apply {kind: (enabled, seconds)} to hypridle.conf and restart hypridle"""
    try:
        lines = open(HYPRIDLE_CONF).read().splitlines()
    except OSError:
        return False

    for start, end, kind in _find_blocks(lines):
        enabled, seconds = settings[kind]
        for i in range(start, end + 1):
            # Normalize to uncommented content first
            content = re.sub(r"^(\s*)#\s?", r"\1", lines[i])
            if re.search(r"timeout\s*=\s*\d+", content):
                indent = re.match(r"\s*", content).group(0)
                minutes = seconds / 60
                human = (f"{minutes:.0f}min" if minutes == int(minutes)
                         else f"{minutes:.1f}min")
                content = f"{indent}timeout = {seconds}  # {human}"
            lines[i] = content if enabled else "# " + content

    with open(HYPRIDLE_CONF, "w") as f:
        f.write("\n".join(lines) + "\n")

    subprocess.run(["pkill", "-x", "hypridle"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["hypridle"], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


class IdlePopover(Gtk.Popover):
    """Enable switches + minute spinners for screen-off / lock / suspend"""

    ROWS = (
        ("dpms", "󰶐", "Screen off"),
        ("lock", "󰌾", "Lock"),
        ("suspend", "󰤄", "Suspend"),
    )

    def __init__(self, relative_to):
        super().__init__(relative_to=relative_to,
                         position=Gtk.PositionType.LEFT)
        self.set_name("idle-popover")
        self._controls = {}

        box = Box(orientation="v", spacing=10,
                  style_classes=["idle-popover-box"])
        box.add(Label(style_classes=["homescreen-card-title"],
                      label="󰔛  IDLE TIMERS", h_align="start"))

        for kind, icon, title in self.ROWS:
            row = Box(orientation="h", spacing=10)
            switch = Gtk.Switch(visible=True, valign=Gtk.Align.CENTER)
            spin = Gtk.SpinButton.new_with_range(1, 180, 1)
            spin.set_visible(True)

            row.add(switch)
            row.add(Label(style_classes=["homescreen-detail"],
                          label=f"{icon} {title}", h_align="start"))
            row.add(Box(h_expand=True))
            row.add(spin)
            row.add(Label(style_classes=["homescreen-hint"], label="min",
                          v_align="center"))
            box.add(row)
            self._controls[kind] = (switch, spin)

        apply_btn = Button(style_classes=["idle-apply-btn"], label="Apply",
                           on_clicked=self._apply)
        box.add(apply_btn)
        box.show_all()
        self.add(box)

        self.connect("show", self._load)

    def _load(self, *_):
        for kind, (enabled, seconds) in read_settings().items():
            if kind not in self._controls:
                continue
            switch, spin = self._controls[kind]
            switch.set_active(enabled)
            spin.set_value(max(1, round(seconds / 60)))

    def _apply(self, *_):
        settings = {
            kind: (switch.get_active(), int(spin.get_value()) * 60)
            for kind, (switch, spin) in self._controls.items()
        }
        write_settings(settings)
        self.popdown()
