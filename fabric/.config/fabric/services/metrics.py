"""
Metrics Provider Service
Centralized system metrics collection with debounced updates.
Provides CPU, memory, disk, network, and battery information.

Usage:
    from services.metrics import get_metrics_provider

    metrics = get_metrics_provider()

    # Get current values
    cpu = metrics.cpu_percent
    mem = metrics.memory_percent

    # Listen for updates
    metrics.connect("cpu-updated", lambda m, val: print(f"CPU: {val}%"))
    metrics.connect("memory-updated", lambda m, val: print(f"RAM: {val}%"))
"""

import subprocess
import os
from typing import Dict, Optional, List
from fabric.core.service import Service, Signal, Property
from gi.repository import GLib


class NetworkStats:
    """Network interface statistics"""

    def __init__(self, interface: str = ""):
        self.interface = interface
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.rx_speed = 0.0  # bytes/sec
        self.tx_speed = 0.0  # bytes/sec

    @property
    def rx_speed_formatted(self) -> str:
        return self._format_speed(self.rx_speed)

    @property
    def tx_speed_formatted(self) -> str:
        return self._format_speed(self.tx_speed)

    def _format_speed(self, speed: float) -> str:
        """Format speed in human-readable format"""
        if speed >= 1024 * 1024:
            return f"{speed / (1024 * 1024):.1f} MB/s"
        elif speed >= 1024:
            return f"{speed / 1024:.1f} KB/s"
        else:
            return f"{speed:.0f} B/s"


class DiskStats:
    """Disk usage statistics"""

    def __init__(self, mountpoint: str = "/"):
        self.mountpoint = mountpoint
        self.total = 0
        self.used = 0
        self.free = 0
        self.percent = 0.0

    @property
    def total_formatted(self) -> str:
        return self._format_size(self.total)

    @property
    def used_formatted(self) -> str:
        return self._format_size(self.used)

    @property
    def free_formatted(self) -> str:
        return self._format_size(self.free)

    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


class BatteryStats:
    """Battery status information"""

    def __init__(self):
        self.present = False
        self.percent = 100
        self.charging = False
        self.time_remaining = ""  # "2h 30m" or ""
        self.power_source = "AC"  # "AC" or "Battery"

    @property
    def icon(self) -> str:
        """Get appropriate battery icon"""
        if not self.present:
            return "󰚥"  # No battery

        if self.charging:
            return "󰂄"  # Charging

        if self.percent >= 90:
            return "󰁹"
        elif self.percent >= 70:
            return "󰂁"
        elif self.percent >= 50:
            return "󰁿"
        elif self.percent >= 30:
            return "󰁽"
        elif self.percent >= 10:
            return "󰁻"
        else:
            return "󰂃"  # Critical


class MetricsProvider(Service):
    """
    Centralized metrics service with configurable update intervals.
    Uses /proc and /sys filesystem for efficient data collection.
    """

    @Signal
    def cpu_updated(self, value: float) -> None:
        """Emitted when CPU usage is updated"""
        pass

    @Signal
    def memory_updated(self, value: float) -> None:
        """Emitted when memory usage is updated"""
        pass

    @Signal
    def disk_updated(self) -> None:
        """Emitted when disk usage is updated"""
        pass

    @Signal
    def network_updated(self) -> None:
        """Emitted when network stats are updated"""
        pass

    @Signal
    def battery_updated(self) -> None:
        """Emitted when battery status is updated"""
        pass

    _instance = None

    @classmethod
    def get_instance(cls) -> "MetricsProvider":
        """Get the singleton MetricsProvider instance"""
        if cls._instance is None:
            cls._instance = MetricsProvider()
        return cls._instance

    def __init__(
        self,
        cpu_interval: int = 2000,
        memory_interval: int = 5000,
        disk_interval: int = 30000,
        network_interval: int = 1000,
        battery_interval: int = 10000,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Update intervals (ms)
        self._cpu_interval = cpu_interval
        self._memory_interval = memory_interval
        self._disk_interval = disk_interval
        self._network_interval = network_interval
        self._battery_interval = battery_interval

        # Current values
        self._cpu_percent = 0.0
        self._memory_percent = 0.0
        self._memory_used = 0
        self._memory_total = 0
        self._disk_stats: Dict[str, DiskStats] = {}
        self._network_stats = NetworkStats()
        self._battery_stats = BatteryStats()

        # For CPU calculation
        self._last_cpu_times = None

        # For network speed calculation
        self._last_net_rx = 0
        self._last_net_tx = 0
        self._last_net_time = 0

        # Timeout IDs
        self._timeout_ids: List[int] = []

        # Start update loops
        self._start_updates()

    def _start_updates(self) -> None:
        """Start all update loops"""
        # Initial updates
        self._update_cpu()
        self._update_memory()
        self._update_disk()
        self._update_network()
        self._update_battery()

        # Schedule periodic updates
        self._timeout_ids.append(
            GLib.timeout_add(self._cpu_interval, self._update_cpu)
        )
        self._timeout_ids.append(
            GLib.timeout_add(self._memory_interval, self._update_memory)
        )
        self._timeout_ids.append(
            GLib.timeout_add(self._disk_interval, self._update_disk)
        )
        self._timeout_ids.append(
            GLib.timeout_add(self._network_interval, self._update_network)
        )
        self._timeout_ids.append(
            GLib.timeout_add(self._battery_interval, self._update_battery)
        )

    def stop(self) -> None:
        """Stop all update loops"""
        for timeout_id in self._timeout_ids:
            GLib.source_remove(timeout_id)
        self._timeout_ids.clear()

    # CPU Metrics

    def _update_cpu(self) -> bool:
        """Update CPU usage from /proc/stat"""
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()

            parts = line.split()
            if parts[0] != "cpu":
                return True

            # cpu user nice system idle iowait irq softirq
            times = [int(x) for x in parts[1:8]]
            idle = times[3] + times[4]  # idle + iowait
            total = sum(times)

            if self._last_cpu_times:
                last_idle, last_total = self._last_cpu_times
                idle_diff = idle - last_idle
                total_diff = total - last_total

                if total_diff > 0:
                    self._cpu_percent = 100.0 * (1 - idle_diff / total_diff)
                    self.emit("cpu-updated", self._cpu_percent)

            self._last_cpu_times = (idle, total)

        except Exception as e:
            print(f"Error reading CPU stats: {e}")

        return True

    @Property(float, "readable", default_value=0.0)
    def cpu_percent(self) -> float:
        return self._cpu_percent

    # Memory Metrics

    def _update_memory(self) -> bool:
        """Update memory usage from /proc/meminfo"""
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()

            mem_info = {}
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    value = int(parts[1]) * 1024  # Convert KB to bytes
                    mem_info[key] = value

            total = mem_info.get("MemTotal", 0)
            free = mem_info.get("MemFree", 0)
            buffers = mem_info.get("Buffers", 0)
            cached = mem_info.get("Cached", 0)
            sreclaimable = mem_info.get("SReclaimable", 0)

            # Used = Total - Free - Buffers - Cached - SReclaimable
            used = total - free - buffers - cached - sreclaimable

            self._memory_total = total
            self._memory_used = used

            if total > 0:
                self._memory_percent = 100.0 * used / total
                self.emit("memory-updated", self._memory_percent)

        except Exception as e:
            print(f"Error reading memory stats: {e}")

        return True

    @Property(float, "readable", default_value=0.0)
    def memory_percent(self) -> float:
        return self._memory_percent

    @Property(int, "readable", default_value=0)
    def memory_used(self) -> int:
        return self._memory_used

    @Property(int, "readable", default_value=0)
    def memory_total(self) -> int:
        return self._memory_total

    @property
    def memory_used_formatted(self) -> str:
        return self._format_size(self._memory_used)

    @property
    def memory_total_formatted(self) -> str:
        return self._format_size(self._memory_total)

    # Disk Metrics

    def _update_disk(self) -> bool:
        """Update disk usage using statvfs"""
        try:
            # Check common mountpoints
            for mountpoint in ["/", "/home"]:
                if os.path.exists(mountpoint):
                    stat = os.statvfs(mountpoint)

                    total = stat.f_blocks * stat.f_frsize
                    free = stat.f_bfree * stat.f_frsize
                    used = total - free

                    disk = DiskStats(mountpoint)
                    disk.total = total
                    disk.free = free
                    disk.used = used
                    disk.percent = 100.0 * used / total if total > 0 else 0

                    self._disk_stats[mountpoint] = disk

            self.emit("disk-updated")

        except Exception as e:
            print(f"Error reading disk stats: {e}")

        return True

    def get_disk_stats(self, mountpoint: str = "/") -> Optional[DiskStats]:
        return self._disk_stats.get(mountpoint)

    @Property(float, "readable", default_value=0.0)
    def disk_percent(self) -> float:
        """Get root disk usage percentage"""
        disk = self._disk_stats.get("/")
        return disk.percent if disk else 0.0

    # Network Metrics

    def _update_network(self) -> bool:
        """Update network stats from /proc/net/dev"""
        try:
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()[2:]  # Skip headers

            rx_total = 0
            tx_total = 0
            active_interface = ""

            for line in lines:
                parts = line.split()
                if len(parts) < 10:
                    continue

                interface = parts[0].rstrip(":")

                # Skip loopback
                if interface == "lo":
                    continue

                rx = int(parts[1])
                tx = int(parts[9])

                # Find active interface (one with traffic)
                if rx > 0 or tx > 0:
                    rx_total += rx
                    tx_total += tx
                    if not active_interface:
                        active_interface = interface

            # Calculate speed
            current_time = GLib.get_monotonic_time() / 1000000.0  # seconds

            if self._last_net_time > 0:
                time_diff = current_time - self._last_net_time
                if time_diff > 0:
                    self._network_stats.rx_speed = (rx_total - self._last_net_rx) / time_diff
                    self._network_stats.tx_speed = (tx_total - self._last_net_tx) / time_diff

            self._network_stats.interface = active_interface
            self._network_stats.rx_bytes = rx_total
            self._network_stats.tx_bytes = tx_total

            self._last_net_rx = rx_total
            self._last_net_tx = tx_total
            self._last_net_time = current_time

            self.emit("network-updated")

        except Exception as e:
            print(f"Error reading network stats: {e}")

        return True

    @property
    def network_stats(self) -> NetworkStats:
        return self._network_stats

    # Battery Metrics

    def _update_battery(self) -> bool:
        """Update battery status from /sys/class/power_supply"""
        try:
            battery_path = "/sys/class/power_supply/BAT0"
            if not os.path.exists(battery_path):
                battery_path = "/sys/class/power_supply/BAT1"

            if not os.path.exists(battery_path):
                self._battery_stats.present = False
                self.emit("battery-updated")
                return True

            self._battery_stats.present = True

            # Read capacity
            capacity_file = os.path.join(battery_path, "capacity")
            if os.path.exists(capacity_file):
                with open(capacity_file, "r") as f:
                    self._battery_stats.percent = int(f.read().strip())

            # Read status
            status_file = os.path.join(battery_path, "status")
            if os.path.exists(status_file):
                with open(status_file, "r") as f:
                    status = f.read().strip()
                    self._battery_stats.charging = status in ["Charging", "Full"]
                    self._battery_stats.power_source = "AC" if self._battery_stats.charging else "Battery"

            self.emit("battery-updated")

        except Exception as e:
            print(f"Error reading battery stats: {e}")

        return True

    @property
    def battery_stats(self) -> BatteryStats:
        return self._battery_stats

    @Property(int, "readable", default_value=100)
    def battery_percent(self) -> int:
        return self._battery_stats.percent

    @Property(bool, "readable", default_value=False)
    def battery_charging(self) -> bool:
        return self._battery_stats.charging

    # Utility methods

    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


# Global singleton accessor
_metrics_provider = None


def get_metrics_provider() -> MetricsProvider:
    """Get the global MetricsProvider instance"""
    global _metrics_provider
    if _metrics_provider is None:
        _metrics_provider = MetricsProvider.get_instance()
    return _metrics_provider
