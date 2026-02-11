"""
Compact Bar Section
Simple bar showing:
- Workspaces (left)
- Clock (right)
"""

from fabric.widgets.box import Box
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.button import Button
from fabric.widgets.datetime import DateTime
from fabric.hyprland.widgets import HyprlandWorkspaces, WorkspaceButton
from gi.repository import Gtk

from services.config import get_config
from services.workspace_manager import WorkspaceManagerService


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
            self.set_label(f"{self.app.icon} ")
            self.add_style_class("active")
        elif status == "idle":
            self.set_label(f"{self.app.icon} ")
            self.add_style_class("idle")
        else:
            self.set_label(f"{self.app.icon}")
            self.add_style_class("empty")

    def on_clicked(self, *args):
        """Handle button click"""
        self.workspace_manager.toggle_app(self.app_name)


class CompactBar(CenterBox):
    """
    Simple bar with workspaces and clock.
    Layout: [Workspaces + Special] --- [Clock]
    """

    def __init__(self, **kwargs):
        self.config = get_config()
        self.workspace_manager = WorkspaceManagerService()

        # Build the sections
        left_section = self._build_left_section()
        right_section = self._build_right_section()

        # Remove h_expand from kwargs if present
        kwargs.pop('h_expand', None)

        super().__init__(
            name="compact-bar",
            orientation=Gtk.Orientation.HORIZONTAL,
            start_children=left_section,
            end_children=right_section,
            **kwargs
        )

        # Force horizontal expansion and fill alignment
        self.set_hexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.CENTER)

    def _build_left_section(self):
        """Build left section: workspaces + special buttons"""
        return Box(
            name="compact-left",
            orientation="h",
            spacing=8,
            children=[
                self._build_workspaces(),
                self._build_special_buttons(),
            ]
        )

    def _build_workspaces(self):
        """Build regular workspace buttons"""
        workspace_count = self.config.workspaces_count
        max_workspaces = self.config.workspaces_dynamic_max

        predefined_buttons = [
            WorkspaceButton(id=i, label=str(i))
            for i in range(1, workspace_count + 1)
        ]

        def workspace_button_factory(workspace_id: int):
            if workspace_id >= 11:
                return None
            if workspace_count < workspace_id <= max_workspaces:
                return WorkspaceButton(id=workspace_id, label=str(workspace_id))
            return None

        return HyprlandWorkspaces(
            name="workspaces",
            buttons=predefined_buttons,
            buttons_factory=workspace_button_factory
        )

    def _build_special_buttons(self):
        """Build special workspace buttons from config"""
        special_workspaces = self.config.special_workspaces
        buttons = []

        for app_name, app_config in special_workspaces.items():
            if app_config.get("enabled", True):
                buttons.append(
                    SpecialWorkspaceButton(app_name, self.workspace_manager)
                )

        return Box(
            name="special-workspaces",
            orientation="h",
            spacing=4,
            children=buttons
        )

    def _build_right_section(self):
        """Build right section: notification button + clock"""
        return Box(
            name="compact-right",
            orientation="h",
            spacing=8,
            children=[
                self._build_notification_button(),
                self._build_clock(),
            ]
        )

    def _build_notification_button(self):
        """Build notification center button"""
        import subprocess

        def toggle_notifications(*_):
            subprocess.Popen(["swaync-client", "-t"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return Button(
            name="notification-button",
            label="󰂚",  # Bell icon
            on_clicked=toggle_notifications,
        )

    def _build_clock(self):
        """Build clock/datetime display"""
        return DateTime(
            formatters=[
                self.config.clock_format,
                "%A",
                "%d-%m-%Y"
            ],
            interval=self.config.clock_update_interval,
            name="clock",
        )
