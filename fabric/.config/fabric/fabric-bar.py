"""
Fabric Main Bar - Waybar Replacement
A custom bar for Hyprland using the Fabric framework
"""

import os
from fabric import Application
from fabric.utils import compile_css
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.datetime import DateTime
from fabric.widgets.wayland import WaylandWindow
from fabric.hyprland.widgets import HyprlandWorkspaces, WorkspaceButton, HyprlandActiveWindow
from services.workspace_manager import WorkspaceManagerService
from widgets.audio import get_audio_widget
from widgets.network import get_network_widget
from widgets.battery import get_battery_widget
from widgets.power_menu import get_power_menu_widget
from widgets.system_tray import get_system_tray_widget
from widgets.utility import get_utility_widget


class SpecialWorkspaceButton(Button):
    """A button for special workspace apps (Discord, VS Code, etc.)"""

    def __init__(self, app_name: str, workspace_manager: WorkspaceManagerService, **kwargs):
        self.app_name = app_name
        self.workspace_manager = workspace_manager
        self.app = workspace_manager.apps[app_name]

        super().__init__(
            label="",
            name=f"special-{app_name}",
            on_clicked=self.on_clicked,
            **kwargs
        )

        # Connect to workspace manager signals
        self.workspace_manager.connect(
            "app-status-changed",
            lambda service, changed_app: self.update_status() if changed_app == app_name else None
        )

        # Initial update
        self.update_status()

    def update_status(self):
        """Update button appearance based on app status"""
        status = self.workspace_manager.get_app_status(self.app_name)

        # Remove all state classes
        self.remove_style_class("active")
        self.remove_style_class("idle")
        self.remove_style_class("empty")

        # Update label with icon and indicator, add appropriate class
        if status == "active":
            # App running and user is on that workspace
            self.set_label(f"{self.app.icon} ●")
            self.add_style_class("active")
        elif status == "idle":
            # App running but user is on different workspace
            self.set_label(f"{self.app.icon} ●")
            self.add_style_class("idle")
        else:  # empty
            # App not running
            self.set_label(f"{self.app.icon}")
            self.add_style_class("empty")

    def on_clicked(self, *args):
        """Handle button click"""
        self.workspace_manager.toggle_app(self.app_name)


class MainBar(WaylandWindow):
    """Main status bar window"""

    def __init__(self, **kwargs):
        super().__init__(
            layer="top",
            anchor="left top right",
            exclusivity="auto",
            name="main-bar",
            visible=True,
            **kwargs
        )

        # Initialize workspace manager
        self.workspace_manager = WorkspaceManagerService()

        # Initialize clock widget (must be stored as instance variable)
        self.date_time = DateTime(
            formatters=["%H:%M:%S", "%A", "%m-%d-%Y"],
            interval=100,  # Update every 100ms for more accurate time display
            name="clock",
        )

        # Build the bar layout
        self.children = self.build_layout()

    def build_layout(self):
        """Build the bar layout"""
        return CenterBox(
            name="bar-content",
            start_children=self.build_left_section(),
            center_children=self.build_center_section(),
            end_children=self.build_right_section(),
        )

    def build_left_section(self):
        """Build left section: workspaces + special buttons + active window"""
        return Box(
            name="left-section",
            orientation="h",
            spacing=8,
            children=[
                self.build_workspaces(),
                self.build_special_buttons(),
                self.build_active_window(),
            ]
        )

    def build_workspaces(self):
        """Build regular workspace buttons (1-5, plus active ones 6-10)"""
        # Create predefined buttons for workspaces 1-5
        # These will always show even when empty
        predefined_buttons = [
            WorkspaceButton(id=i, label=str(i))
            for i in range(1, 6)  # Creates buttons 1-5
        ]

        def workspace_button_factory(workspace_id: int):
            # Ignore special workspaces (11-14)
            if workspace_id >= 11:
                return None
            # For workspaces 6-10, only create button if they become active
            # (factory is called when workspace is opened)
            if 6 <= workspace_id <= 10:
                return WorkspaceButton(
                    id=workspace_id,
                    label=str(workspace_id)
                )
            # For 1-5, they're already in predefined_buttons
            return None

        return HyprlandWorkspaces(
            name="workspaces",
            buttons=predefined_buttons,  # Always show 1-5
            buttons_factory=workspace_button_factory  # Dynamically create 6-10
        )

    def build_special_buttons(self):
        """Build special workspace buttons"""
        return Box(
            name="special-workspaces",
            orientation="h",
            spacing=4,
            children=[
                SpecialWorkspaceButton("discord", self.workspace_manager),
                SpecialWorkspaceButton("vscode", self.workspace_manager),
                SpecialWorkspaceButton("minecraft", self.workspace_manager),
                SpecialWorkspaceButton("steam", self.workspace_manager),
            ]
        )

    def build_active_window(self):
        """Build active window title display"""
        return HyprlandActiveWindow(
            name="active-window",
        )

    def build_center_section(self):
        """Build center section: media info"""
        # TODO: Implement media player widget
        return Label(
            label="",
            name="media-info"
        )

    def build_right_section(self):
        """Build right section: widget buttons + clock"""
        return Box(
            name="right-section",
            orientation="h",
            spacing=8,
            children=[
                self.build_widget_buttons(),
                self.build_clock(),
            ]
        )

    def build_widget_buttons(self):
        """Build buttons that trigger popup widgets"""
        return Box(
            name="widget-buttons",
            orientation="h",
            spacing=4,
            children=[
                Button(
                    label="🔊",
                    name="audio-button",
                    tooltip_text="Audio Control",
                    on_clicked=lambda *_: get_audio_widget().toggle()
                ),
                Button(
                    label="📡",
                    name="network-button",
                    tooltip_text="Network & Bluetooth",
                    on_clicked=lambda *_: get_network_widget().toggle()
                ),
                Button(
                    label="🔋",
                    name="battery-button",
                    tooltip_text="Battery & Power",
                    on_clicked=lambda *_: get_battery_widget().toggle()
                ),
                Button(
                    label="📋",
                    name="tray-button",
                    tooltip_text="System Tray",
                    on_clicked=lambda *_: get_system_tray_widget().toggle()
                ),
                Button(
                    label="⚙️",
                    name="utility-button",
                    tooltip_text="Utilities",
                    on_clicked=lambda *_: get_utility_widget().toggle()
                ),
                Button(
                    label="⏻",
                    name="power-button",
                    tooltip_text="Power Menu",
                    on_clicked=lambda *_: get_power_menu_widget().toggle()
                ),
            ]
        )

    def build_clock(self):
        """Build clock/datetime display"""
        return self.date_time


if __name__ == "__main__":
    # Get the directory of this script for loading stylesheets
    script_dir = os.path.dirname(os.path.abspath(__file__))
    style_file = os.path.join(script_dir, "style.css")

    # Create the main bar
    bar = MainBar()

    # Create the application
    app = Application("fabric-bar", bar)

    # Load and compile stylesheet if it exists
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
