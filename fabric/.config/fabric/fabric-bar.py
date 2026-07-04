"""
Fabric Bar - Simple Hyprland bar
Features:
- Workspaces with special workspace buttons
- Multi-monitor support via MonitorManager
- Configuration-driven via config.json
- Dynamic theming via Matugen
"""

import os
from gi.repository import Gio, GLib
from fabric import Application
from fabric.utils import compile_css

# Import services
from services.config import get_config
from services.monitor_manager import get_monitor_manager

# Import the bar system
from notch_bar import create_notch_windows
from desktop import create_homescreens


def create_bar_for_monitors():
    """Create bar instances for configured monitors"""
    config = get_config()
    monitor_manager = get_monitor_manager()

    windows = []
    monitors = monitor_manager.get_monitors()

    # Get configured monitor setting
    bar_monitor = config.bar_monitor

    if bar_monitor == -1:
        # Show on all monitors
        for monitor in monitors:
            bar, _ = create_notch_windows(monitor=monitor.id)
            windows.append(bar)
            monitor_manager.register_instances(monitor.id, {'bar': bar})
    else:
        # Show on specific monitor
        bar, _ = create_notch_windows(monitor=bar_monitor)
        windows.append(bar)
        monitor_manager.register_instances(bar_monitor, {'bar': bar})

    return windows


if __name__ == "__main__":
    # Get the directory of this script for loading stylesheets
    script_dir = os.path.dirname(os.path.abspath(__file__))
    style_file = os.path.join(script_dir, "style.css")

    # Get configuration
    config = get_config()

    # Create bar windows for monitors
    windows = create_bar_for_monitors()

    if not windows:
        # Fallback: create bar for monitor 0
        bar, _ = create_notch_windows(monitor=0)
        windows = [bar]

    # Filter out None values
    windows = [w for w in windows if w is not None]

    # Homescreen widget layer (shown when the active workspace is empty)
    homescreen_manager = create_homescreens(get_monitor_manager().get_monitors())
    if homescreen_manager:
        windows.extend(homescreen_manager.windows)

    # Create the application with all windows
    app = Application("fabric-bar", *windows)

    # Define CSS reload function
    def set_css():
        """Reload CSS from style.css"""
        if os.path.exists(style_file):
            with open(style_file, 'r') as f:
                css_content = f.read()
            compiled_css = compile_css(css_content, base_path=os.path.dirname(style_file))
            app.set_stylesheet_from_string(compiled_css)
            print("CSS reloaded successfully")

    # Expose set_css on app object
    app.set_css = set_css

    # Set up file watchers for CSS files
    css_files_to_watch = [
        os.path.join(script_dir, "colors.css"),
        os.path.join(script_dir, "style.css"),
    ]

    # Also watch modular CSS files
    styles_dir = os.path.join(script_dir, "styles")
    if os.path.exists(styles_dir):
        for filename in os.listdir(styles_dir):
            if filename.endswith(".css"):
                css_files_to_watch.append(os.path.join(styles_dir, filename))

    app._css_monitors = []

    for css_file in css_files_to_watch:
        if os.path.exists(css_file):
            gfile = Gio.File.new_for_path(css_file)
            monitor = gfile.monitor_file(Gio.FileMonitorFlags.NONE, None)

            def on_css_changed(monitor, file, other_file, event_type):
                if event_type == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
                    print(f"{file.get_path()} changed, reloading CSS...")
                    GLib.idle_add(set_css)

            monitor.connect("changed", on_css_changed)
            app._css_monitors.append(monitor)

    print(f"Watching {len(css_files_to_watch)} CSS files for changes")

    # Initial CSS load
    if os.path.exists(style_file):
        with open(style_file, 'r') as f:
            css_content = f.read()

        # Compile FASS to GTK CSS
        compiled_css = compile_css(css_content, base_path=os.path.dirname(style_file))

        # Debug: Save compiled CSS to see what's being generated
        debug_file = os.path.join(os.path.dirname(style_file), "compiled_debug.css")
        with open(debug_file, 'w') as f:
            f.write(compiled_css)
        print(f"Compiled CSS saved to: {debug_file}")

        # Load the compiled CSS
        app.set_stylesheet_from_string(compiled_css)

    # Run the application
    app.run()
