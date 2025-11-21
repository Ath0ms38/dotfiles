"""
Power Menu Widget
Shutdown, reboot, logout, lock, and sleep options
"""

import subprocess
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.wayland import WaylandWindow


class PowerMenuWidget(WaylandWindow):
    """Power menu popup widget"""

    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="top right",
            margin="50px 20px 0px 0px",
            keyboard_mode="on-demand",
            name="power-menu-widget",
            visible=False,
            **kwargs
        )

        # Build widget
        self.children = self.build_content()

    def execute_power_action(self, action: str):
        """Execute a power action"""
        try:
            if action == "shutdown":
                subprocess.run(["systemctl", "poweroff"], check=False)
            elif action == "reboot":
                subprocess.run(["systemctl", "reboot"], check=False)
            elif action == "logout":
                # For Hyprland
                subprocess.run(["hyprctl", "dispatch", "exit"], check=False)
            elif action == "lock":
                # Try common lock commands
                for cmd in [["hyprlock"], ["swaylock"], ["gtklock"]]:
                    try:
                        subprocess.run(cmd, check=False)
                        break
                    except FileNotFoundError:
                        continue
            elif action == "sleep":
                subprocess.run(["systemctl", "suspend"], check=False)

            # Hide the power menu after action
            self.hide()

        except Exception as e:
            print(f"Error executing power action '{action}': {e}")

    def build_power_button(self, icon: str, label: str, action: str, color: str):
        """Build a power action button"""
        return Button(
            child=Box(
                orientation="v",
                spacing=8,
                children=[
                    Label(
                        label=icon,
                        style=f"font-size: 32px; color: {color};"
                    ),
                    Label(
                        label=label,
                        style="font-size: 12px;"
                    ),
                ]
            ),
            name=f"power-{action}",
            on_clicked=lambda *_: self.execute_power_action(action),
            style="min-width: 100px; min-height: 100px;"
        )

    def build_content(self):
        """Build the widget content"""
        buttons_row1 = Box(
            orientation="h",
            spacing=12,
            name="power-buttons-row1",
            children=[
                self.build_power_button("⏻", "Shutdown", "shutdown", "#ff6b6b"),
                self.build_power_button("", "Reboot", "reboot", "#ffd966"),
                self.build_power_button("󰍃", "Logout", "logout", "#a4e88d"),
            ]
        )

        buttons_row2 = Box(
            orientation="h",
            spacing=12,
            name="power-buttons-row2",
            children=[
                self.build_power_button("", "Lock", "lock", "#74c7ec"),
                self.build_power_button("󰒲", "Sleep", "sleep", "#cba6f7"),
            ]
        )

        content = Box(
            orientation="v",
            spacing=16,
            name="power-menu-content",
            children=[
                Label(
                    label="⏻ Power Menu",
                    name="power-menu-title",
                    style="font-size: 16px; font-weight: bold;"
                ),
                buttons_row1,
                buttons_row2,
                Label(
                    label="Click an option to proceed",
                    name="power-menu-hint",
                    style="font-size: 11px; opacity: 0.7; margin-top: 8px;"
                ),
            ]
        )

        return Box(
            name="power-menu-container",
            orientation="v",
            children=content,
            style="padding: 20px; min-width: 350px;"
        )

    def toggle(self):
        """Toggle widget visibility"""
        if self.get_visible():
            self.hide()
        else:
            self.show_all()


# Create singleton instance
power_menu_widget = None


def get_power_menu_widget():
    """Get or create the power menu widget singleton"""
    global power_menu_widget
    if power_menu_widget is None:
        power_menu_widget = PowerMenuWidget()
    return power_menu_widget
