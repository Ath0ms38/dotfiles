"""
Workspace Manager Service for Hyprland
Manages special workspaces for Discord, VS Code, Minecraft, and Steam
"""

import json
import subprocess
from fabric.core.service import Service, Signal, Property
from fabric.hyprland.service import Hyprland


class WorkspaceApp:
    """Represents an application assigned to a specific workspace"""

    def __init__(self, name: str, workspace_id: int, window_class: str, command: str, icon: str):
        self.name = name
        self.workspace_id = workspace_id
        self.window_class = window_class
        self.command = command
        self.icon = icon


class WorkspaceManagerService(Service):
    """Service for managing special workspace assignments"""

    @Signal
    def app_status_changed(self, app_name: str) -> None:
        """Emitted when an app's status changes"""
        ...

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Define special workspace apps
        self.apps = {
            "discord": WorkspaceApp("discord", 11, "discord", "discord", "󰙯"),
            "vscode": WorkspaceApp("vscode", 12, "Code", "code", "󰨞"),
            "minecraft": WorkspaceApp("minecraft", 13, "org.polymc.PolyMC", "polymc", "󰍳"),
            "steam": WorkspaceApp("steam", 14, "steam", "steam", "󰓓"),
        }

        # Connect to Hyprland events
        self.hyprland = Hyprland()
        self.hyprland.connect("event::workspace", self._on_workspace_change)
        self.hyprland.connect("event::openwindow", self._on_window_open)
        self.hyprland.connect("event::closewindow", self._on_window_close)
        self.hyprland.connect("event::activewindow", self._on_active_window)

    def _on_workspace_change(self, service, event):
        """Handle workspace change events"""
        # Notify all apps that workspace changed
        for app_name in self.apps:
            self.app_status_changed(app_name)

    def _on_window_open(self, service, event):
        """Handle window open events"""
        # Check if opened window belongs to a special app
        for app_name in self.apps:
            self.app_status_changed(app_name)

    def _on_window_close(self, service, event):
        """Handle window close events"""
        for app_name in self.apps:
            self.app_status_changed(app_name)

    def _on_active_window(self, service, event):
        """Handle active window change events"""
        for app_name in self.apps:
            self.app_status_changed(app_name)

    def get_active_workspace_id(self) -> int:
        """Get the currently active workspace ID"""
        try:
            result = Hyprland.send_command("activeworkspace")
            if result and result.is_ok:
                data = json.loads(result.reply)
                workspace_id = data.get("id", 1)
                print(f"[DEBUG get_active_workspace_id] Got workspace ID via Hyprland: {workspace_id}")
                return workspace_id
        except Exception as e:
            print(f"[DEBUG get_active_workspace_id] Hyprland.send_command failed: {e}")

        # Fallback to direct hyprctl call
        try:
            output = subprocess.check_output(["hyprctl", "activeworkspace", "-j"], text=True)
            data = json.loads(output)
            workspace_id = data.get("id", 1)
            print(f"[DEBUG get_active_workspace_id] Got workspace ID via subprocess: {workspace_id}")
            return workspace_id
        except Exception as e:
            print(f"[DEBUG get_active_workspace_id] Subprocess failed: {e}")

        return 1

    def get_windows(self):
        """Get list of all windows"""
        try:
            result = Hyprland.send_command("clients")
            if result and result.is_ok:
                return json.loads(result.reply)
            else:
                # Fallback to subprocess
                output = subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
                return json.loads(output)
        except Exception:
            pass
        return []

    def is_app_running_in_workspace(self, app_name: str) -> bool:
        """Check if app is running in its designated workspace"""
        if app_name not in self.apps:
            return False

        app = self.apps[app_name]
        windows = self.get_windows()

        for window in windows:
            if window.get("class") == app.window_class:
                if window.get("workspace", {}).get("id") == app.workspace_id:
                    return True
        return False

    def is_app_running_elsewhere(self, app_name: str) -> bool:
        """Check if app is running outside its designated workspace"""
        if app_name not in self.apps:
            return False

        app = self.apps[app_name]
        windows = self.get_windows()

        for window in windows:
            if window.get("class") == app.window_class:
                if window.get("workspace", {}).get("id") != app.workspace_id:
                    return True
        return False

    def is_app_running(self, app_name: str) -> bool:
        """Check if app is running anywhere"""
        if app_name not in self.apps:
            return False

        app = self.apps[app_name]
        windows = self.get_windows()

        for window in windows:
            if window.get("class") == app.window_class:
                return True
        return False

    def get_app_status(self, app_name: str) -> str:
        """
        Get the status of an app
        Returns: 'active', 'idle', 'empty'
        """
        if app_name not in self.apps:
            return "empty"

        app = self.apps[app_name]
        active_workspace = self.get_active_workspace_id()
        app_in_workspace = self.is_app_running_in_workspace(app_name)

        print(f"[DEBUG get_app_status] {app_name}: active_ws={active_workspace}, app_ws={app.workspace_id}, in_workspace={app_in_workspace}")

        if app_in_workspace:
            if active_workspace == app.workspace_id:
                return "active"
            return "idle"

        if self.is_app_running_elsewhere(app_name):
            return "idle"

        return "empty"

    def toggle_app(self, app_name: str):
        """
        Toggle an app - launch it if not running, otherwise switch to/move to designated workspace
        """
        if app_name not in self.apps:
            return

        app = self.apps[app_name]
        windows = self.get_windows()

        # Check if app is running anywhere
        is_running = self.is_app_running(app_name)

        if is_running:
            # App is running - move it to designated workspace if not already there
            if not self.is_app_running_in_workspace(app_name):
                for window in windows:
                    if window.get("class") == app.window_class:
                        address = window.get("address", "")
                        if address:
                            # Move window to designated workspace
                            Hyprland.send_command(f"dispatch movetoworkspacesilent {app.workspace_id},address:{address}")
        else:
            # App is not running - launch it in designated workspace
            subprocess.Popen(
                ["hyprctl", "dispatch", "exec", f"[workspace {app.workspace_id}] {app.command}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        # Switch to the designated workspace
        Hyprland.send_command(f"dispatch workspace {app.workspace_id}")

        # Emit status change
        self.app_status_changed(app_name)
