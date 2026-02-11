"""
Monitor Manager Service
Handles multi-monitor support for the Fabric bar.
Tracks monitors, manages per-monitor component instances,
and handles focus changes.

Usage:
    from services.monitor_manager import get_monitor_manager

    manager = get_monitor_manager()

    # Get all monitors
    monitors = manager.get_monitors()

    # Register bar instances for a monitor
    manager.register_instances(monitor_id=0, instances={
        'bar': bar,
        'popups': [audio_popup, network_popup]
    })

    # Listen for monitor changes
    manager.connect("monitor-added", on_monitor_added)
    manager.connect("monitor-removed", on_monitor_removed)
    manager.connect("focus-changed", on_focus_changed)
"""

import subprocess
import json
from typing import Dict, List, Any, Optional
from fabric.core.service import Service, Signal, Property
from gi.repository import GLib


class Monitor:
    """Represents a physical monitor"""

    def __init__(
        self,
        id: int,
        name: str,
        width: int,
        height: int,
        x: int,
        y: int,
        scale: float = 1.0,
        refresh_rate: float = 60.0,
        focused: bool = False
    ):
        self.id = id
        self.name = name
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.scale = scale
        self.refresh_rate = refresh_rate
        self.focused = focused

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def position(self) -> tuple:
        return (self.x, self.y)

    def __repr__(self):
        return f"Monitor({self.id}, {self.name}, {self.resolution}@{self.x},{self.y})"


class MonitorManager(Service):
    """
    Manages monitors and per-monitor component instances.
    Uses Hyprland IPC to get monitor information.
    """

    @Signal
    def monitor_added(self, monitor_id: int) -> None:
        """Emitted when a new monitor is connected"""
        pass

    @Signal
    def monitor_removed(self, monitor_id: int) -> None:
        """Emitted when a monitor is disconnected"""
        pass

    @Signal
    def focus_changed(self, monitor_id: int) -> None:
        """Emitted when focused monitor changes"""
        pass

    @Signal
    def monitors_updated(self) -> None:
        """Emitted when monitor list is updated"""
        pass

    _instance = None

    @classmethod
    def get_instance(cls) -> "MonitorManager":
        """Get the singleton MonitorManager instance"""
        if cls._instance is None:
            cls._instance = MonitorManager()
        return cls._instance

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._monitors: Dict[int, Monitor] = {}
        self._instances: Dict[int, Dict[str, Any]] = {}
        self._focused_monitor_id: int = 0
        self._poll_timeout_id = None

        # Initial monitor detection
        self._update_monitors()

        # Set up Hyprland event listener for monitor changes
        self._setup_hyprland_listener()

    def _update_monitors(self) -> None:
        """Update monitor list from Hyprland"""
        try:
            result = subprocess.run(
                ["hyprctl", "monitors", "-j"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return

            monitors_data = json.loads(result.stdout)
            old_ids = set(self._monitors.keys())
            new_ids = set()

            for mon in monitors_data:
                mon_id = mon.get("id", 0)
                new_ids.add(mon_id)

                monitor = Monitor(
                    id=mon_id,
                    name=mon.get("name", f"Monitor-{mon_id}"),
                    width=mon.get("width", 1920),
                    height=mon.get("height", 1080),
                    x=mon.get("x", 0),
                    y=mon.get("y", 0),
                    scale=mon.get("scale", 1.0),
                    refresh_rate=mon.get("refreshRate", 60.0),
                    focused=mon.get("focused", False)
                )

                if monitor.focused:
                    self._focused_monitor_id = mon_id

                self._monitors[mon_id] = monitor

            # Check for added monitors
            for mon_id in (new_ids - old_ids):
                self.emit("monitor-added", mon_id)

            # Check for removed monitors
            for mon_id in (old_ids - new_ids):
                del self._monitors[mon_id]
                if mon_id in self._instances:
                    del self._instances[mon_id]
                self.emit("monitor-removed", mon_id)

            self.emit("monitors-updated")

        except Exception as e:
            print(f"Error updating monitors: {e}")

    def _setup_hyprland_listener(self) -> None:
        """Set up listener for Hyprland events"""
        try:
            from fabric.hyprland.service import Hyprland

            hyprland = Hyprland()

            # Listen for monitor events
            hyprland.connect("event::monitoradded", lambda _, __: self._update_monitors())
            hyprland.connect("event::monitorremoved", lambda _, __: self._update_monitors())

            # Listen for focus changes
            hyprland.connect("event::focusedmon", self._on_focus_changed)

        except ImportError:
            # Fallback: poll for changes
            self._poll_timeout_id = GLib.timeout_add(5000, self._poll_monitors)

    def _on_focus_changed(self, hyprland, data) -> None:
        """Handle focused monitor change event"""
        try:
            # data format: "monitorname,workspace"
            parts = str(data).split(",")
            if parts:
                monitor_name = parts[0]
                # Find monitor by name
                for mon_id, monitor in self._monitors.items():
                    if monitor.name == monitor_name:
                        if self._focused_monitor_id != mon_id:
                            self._focused_monitor_id = mon_id
                            # Update focus state
                            for m in self._monitors.values():
                                m.focused = (m.id == mon_id)
                            self.emit("focus-changed", mon_id)
                        break
        except Exception:
            pass

    def _poll_monitors(self) -> bool:
        """Fallback polling for monitor changes"""
        self._update_monitors()
        return True  # Continue polling

    @Property(int, "readable", default_value=0)
    def focused_monitor_id(self) -> int:
        """Get the currently focused monitor ID"""
        return self._focused_monitor_id

    @Property(int, "readable", default_value=0)
    def monitor_count(self) -> int:
        """Get the number of monitors"""
        return len(self._monitors)

    def get_monitors(self) -> List[Monitor]:
        """Get list of all monitors"""
        return list(self._monitors.values())

    def get_monitor(self, monitor_id: int) -> Optional[Monitor]:
        """Get a specific monitor by ID"""
        return self._monitors.get(monitor_id)

    def get_focused_monitor(self) -> Optional[Monitor]:
        """Get the currently focused monitor"""
        return self._monitors.get(self._focused_monitor_id)

    def get_primary_monitor(self) -> Optional[Monitor]:
        """Get the primary monitor (usually ID 0 or the one at 0,0)"""
        # Try to find monitor at origin
        for monitor in self._monitors.values():
            if monitor.x == 0 and monitor.y == 0:
                return monitor

        # Fallback to first monitor
        if self._monitors:
            return list(self._monitors.values())[0]

        return None

    def register_instances(self, monitor_id: int, instances: Dict[str, Any]) -> None:
        """
        Register component instances for a monitor.

        Args:
            monitor_id: The monitor ID
            instances: Dict of component name to instance (e.g., {'bar': bar_widget})
        """
        if monitor_id not in self._instances:
            self._instances[monitor_id] = {}

        self._instances[monitor_id].update(instances)

    def get_instances(self, monitor_id: int) -> Dict[str, Any]:
        """Get all registered instances for a monitor"""
        return self._instances.get(monitor_id, {})

    def get_component(self, monitor_id: int, component_name: str) -> Optional[Any]:
        """Get a specific component instance for a monitor"""
        instances = self._instances.get(monitor_id, {})
        return instances.get(component_name)

    def get_all_instances(self, component_name: str) -> List[Any]:
        """Get a specific component from all monitors"""
        instances = []
        for mon_instances in self._instances.values():
            if component_name in mon_instances:
                instances.append(mon_instances[component_name])
        return instances

    def broadcast_to_all(self, component_name: str, method_name: str, *args, **kwargs) -> None:
        """
        Call a method on a component across all monitors.

        Args:
            component_name: Name of the component (e.g., 'bar')
            method_name: Method to call on each instance
            *args, **kwargs: Arguments to pass to the method
        """
        for instance in self.get_all_instances(component_name):
            method = getattr(instance, method_name, None)
            if callable(method):
                try:
                    method(*args, **kwargs)
                except Exception as e:
                    print(f"Error broadcasting {method_name} to {component_name}: {e}")

    def cleanup(self) -> None:
        """Clean up resources"""
        if self._poll_timeout_id:
            GLib.source_remove(self._poll_timeout_id)
            self._poll_timeout_id = None


# Global singleton accessor
_monitor_manager = None


def get_monitor_manager() -> MonitorManager:
    """Get the global MonitorManager instance"""
    global _monitor_manager
    if _monitor_manager is None:
        _monitor_manager = MonitorManager.get_instance()
    return _monitor_manager
