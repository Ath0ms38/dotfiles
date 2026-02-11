#!/usr/bin/env python3
"""
Ax-Shell Style Notch Bar
A separate center notch with dashboard - runs independently from main bar

Usage:
    python ax_notch_bar.py
"""

import os
from gi.repository import Gio, GLib
from fabric import Application
from fabric.utils import compile_css

from ax_notch import create_ax_notch
from services.config import get_config
from services.monitor_manager import get_monitor_manager


def create_notches_for_monitors():
    """Create ax-notch instances for configured monitors"""
    config = get_config()
    monitor_manager = get_monitor_manager()

    windows = []
    monitors = monitor_manager.get_monitors()

    # Get configured monitor setting (use bar_monitor config)
    bar_monitor = config.bar_monitor

    if bar_monitor == -1:
        # Show on all monitors
        for monitor in monitors:
            notch = create_ax_notch(monitor=monitor.id)
            windows.append(notch)
            print(f"Created ax-notch for monitor {monitor.id}")
    else:
        # Show on specific monitor
        notch = create_ax_notch(monitor=bar_monitor)
        windows.append(notch)
        print(f"Created ax-notch for monitor {bar_monitor}")

    return windows


def main():
    # Get script directory for loading stylesheets
    script_dir = os.path.dirname(os.path.abspath(__file__))
    style_file = os.path.join(script_dir, "style.css")

    # Create ax-notch for all configured monitors
    windows = create_notches_for_monitors()

    if not windows:
        # Fallback: create notch for monitor 0
        notch = create_ax_notch(monitor=0)
        windows = [notch]

    # Filter out None values
    windows = [w for w in windows if w is not None]

    # Create application with all windows
    app = Application("ax-notch-bar", *windows)

    # CSS reload function
    def set_css():
        """Reload CSS from style.css"""
        if os.path.exists(style_file):
            with open(style_file, 'r') as f:
                css_content = f.read()
            compiled_css = compile_css(css_content, base_path=os.path.dirname(style_file))
            app.set_stylesheet_from_string(compiled_css)
            print("CSS reloaded")

    app.set_css = set_css

    # Set up CSS file watchers
    css_files = [
        os.path.join(script_dir, "colors.css"),
        os.path.join(script_dir, "style.css"),
    ]

    styles_dir = os.path.join(script_dir, "styles")
    if os.path.exists(styles_dir):
        for filename in os.listdir(styles_dir):
            if filename.endswith(".css"):
                css_files.append(os.path.join(styles_dir, filename))

    app._css_monitors = []

    for css_file in css_files:
        if os.path.exists(css_file):
            gfile = Gio.File.new_for_path(css_file)
            monitor = gfile.monitor_file(Gio.FileMonitorFlags.NONE, None)

            def on_changed(monitor, file, other, event_type):
                if event_type == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
                    print(f"{file.get_path()} changed")
                    GLib.idle_add(set_css)

            monitor.connect("changed", on_changed)
            app._css_monitors.append(monitor)

    print(f"Watching {len(css_files)} CSS files")

    # Initial CSS load
    if os.path.exists(style_file):
        with open(style_file, 'r') as f:
            css_content = f.read()
        compiled_css = compile_css(css_content, base_path=os.path.dirname(style_file))
        app.set_stylesheet_from_string(compiled_css)

    # Run
    print("Ax-Notch Bar started")
    app.run()


if __name__ == "__main__":
    main()
