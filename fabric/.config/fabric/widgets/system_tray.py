"""
System Tray Widget
Displays system tray icons and allows interaction
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.wayland import WaylandWindow
from fabric.system_tray.service import SystemTray
from fabric.system_tray.widgets import SystemTrayItem


class SystemTrayWidget(WaylandWindow):
    """System tray popup widget"""

    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="top right",
            margin="50px 20px 0px 0px",
            keyboard_mode="on-demand",
            name="system-tray-widget",
            visible=False,
            **kwargs
        )

        # Initialize system tray service
        try:
            self.system_tray = SystemTray()
            self.system_tray.connect("changed", lambda *_: self.rebuild_content())
        except Exception as e:
            print(f"Error initializing system tray: {e}")
            self.system_tray = None

        # Build widget
        self.children = self.build_content()

    def build_content(self):
        """Build the widget content"""
        tray_items = []

        if self.system_tray and hasattr(self.system_tray, 'items'):
            for item in self.system_tray.items:
                tray_item = SystemTrayItem(
                    item=item,
                    name="tray-item"
                )
                tray_items.append(tray_item)

        if not tray_items:
            tray_items = [
                Label(
                    label="No system tray items",
                    name="empty-message",
                    style="opacity: 0.7; font-style: italic; padding: 20px;"
                )
            ]

        content = Box(
            orientation="v",
            spacing=8,
            name="system-tray-content",
            children=[
                Label(
                    label=" System Tray",
                    name="system-tray-title",
                    style="font-size: 16px; font-weight: bold;"
                ),
                Box(
                    orientation="v",
                    spacing=4,
                    name="tray-items-list",
                    children=tray_items
                ),
            ]
        )

        return ScrolledWindow(
            min_content_size=(350, 100),
            max_content_size=(350, 500),
            child=content,
            style="padding: 16px;"
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
system_tray_widget = None


def get_system_tray_widget():
    """Get or create the system tray widget singleton"""
    global system_tray_widget
    if system_tray_widget is None:
        system_tray_widget = SystemTrayWidget()
    return system_tray_widget
