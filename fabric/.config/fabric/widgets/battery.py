"""
Battery & Power Management Widget
Shows battery status and power mode controls
"""

import psutil
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.wayland import WaylandWindow
from fabric.utils import bulk_connect
import subprocess


class BatteryWidget(WaylandWindow):
    """Battery & power management popup widget"""

    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="top right",
            margin="50px 20px 0px 0px",
            keyboard_mode="on-demand",
            name="battery-widget",
            visible=False,
            **kwargs
        )

        # Build widget
        self.children = self.build_content()

    def get_battery_info(self):
        """Get battery information using psutil"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = int(battery.percent)
                plugged = battery.power_plugged
                time_left = battery.secsleft

                # Calculate hours and minutes remaining
                if time_left > 0 and time_left != psutil.POWER_TIME_UNLIMITED:
                    hours = time_left // 3600
                    minutes = (time_left % 3600) // 60
                    time_str = f"{hours}h {minutes}m"
                elif plugged:
                    time_str = "Charging"
                else:
                    time_str = "Calculating..."

                return {
                    "percent": percent,
                    "plugged": plugged,
                    "time_str": time_str
                }
        except Exception as e:
            print(f"Error getting battery info: {e}")

        return None

    def get_battery_icon(self, percent, plugged):
        """Get appropriate battery icon"""
        if plugged:
            return "󰂄"  # Charging icon
        elif percent >= 90:
            return "󰁹"
        elif percent >= 70:
            return "󰂀"
        elif percent >= 50:
            return "󰁿"
        elif percent >= 30:
            return "󰁽"
        elif percent >= 10:
            return "󰁼"
        else:
            return "󰂎"  # Low battery

    def set_power_profile(self, profile: str):
        """Set system power profile"""
        try:
            # Try using power-profiles-daemon
            subprocess.run(
                ["powerprofilesctl", "set", profile],
                check=False,
                capture_output=True
            )
            self.rebuild_content()
        except Exception as e:
            print(f"Error setting power profile: {e}")

    def get_current_power_profile(self):
        """Get current power profile"""
        try:
            result = subprocess.run(
                ["powerprofilesctl", "get"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def build_content(self):
        """Build the widget content"""
        battery_info = self.get_battery_info()

        if battery_info:
            percent = battery_info["percent"]
            plugged = battery_info["plugged"]
            time_str = battery_info["time_str"]
            icon = self.get_battery_icon(percent, plugged)

            # Battery status
            status = "Charging" if plugged else "On Battery"

            # Battery color based on level
            if percent >= 70:
                color = "#a4e88d"  # Green
            elif percent >= 30:
                color = "#ffd966"  # Yellow
            else:
                color = "#ff6b6b"  # Red

            battery_section = Box(
                orientation="v",
                spacing=12,
                name="battery-info",
                children=[
                    Label(
                        label=f"{icon} {percent}%",
                        name="battery-percent",
                        style=f"font-size: 48px; font-weight: bold; color: {color};"
                    ),
                    Label(
                        label=status,
                        name="battery-status",
                        style="font-size: 16px; opacity: 0.9;"
                    ),
                    Label(
                        label=f"Time remaining: {time_str}",
                        name="battery-time",
                        style="font-size: 14px; opacity: 0.8;"
                    ),
                ]
            )
        else:
            battery_section = Label(
                label="No battery detected",
                name="no-battery",
                style="font-size: 16px; opacity: 0.7; font-style: italic;"
            )

        # Power profile section
        current_profile = self.get_current_power_profile()

        power_profiles = Box(
            orientation="v",
            spacing=8,
            name="power-profiles",
            children=[
                Label(
                    label="Power Mode",
                    name="section-title",
                    style="font-size: 14px; font-weight: bold; margin-top: 16px;"
                ),
                Box(
                    orientation="h",
                    spacing=8,
                    children=[
                        Button(
                            label="🚀 Performance",
                            name="profile-performance",
                            style_classes=["active"] if current_profile == "performance" else [],
                            on_clicked=lambda *_: self.set_power_profile("performance"),
                            h_expand=True
                        ),
                        Button(
                            label="⚖️ Balanced",
                            name="profile-balanced",
                            style_classes=["active"] if current_profile == "balanced" else [],
                            on_clicked=lambda *_: self.set_power_profile("balanced"),
                            h_expand=True
                        ),
                        Button(
                            label="🔋 Power Saver",
                            name="profile-power-saver",
                            style_classes=["active"] if current_profile == "power-saver" else [],
                            on_clicked=lambda *_: self.set_power_profile("power-saver"),
                            h_expand=True
                        ),
                    ]
                ),
            ]
        )

        content = Box(
            orientation="v",
            spacing=16,
            name="battery-content",
            children=[
                Label(
                    label="󰁹 Battery & Power",
                    name="battery-title",
                    style="font-size: 16px; font-weight: bold;"
                ),
                battery_section,
                power_profiles,
            ]
        )

        return Box(
            name="battery-container",
            orientation="v",
            children=content,
            style="padding: 20px; min-width: 350px;"
        )

    def rebuild_content(self):
        """Rebuild the widget content"""
        self.children = self.build_content()

    def toggle(self):
        """Toggle widget visibility"""
        if self.get_visible():
            self.hide()
        else:
            self.rebuild_content()  # Refresh when opening
            self.show_all()


# Create singleton instance
battery_widget = None


def get_battery_widget():
    """Get or create the battery widget singleton"""
    global battery_widget
    if battery_widget is None:
        battery_widget = BatteryWidget()
    return battery_widget
