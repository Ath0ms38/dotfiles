"""
System Metrics Widget
Displays CPU, RAM, Disk, GPU usage with animated bars
"""

import psutil
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.scale import Scale
from gi.repository import GLib

from . import icons


class MetricsProvider:
    """
    Centralized metrics provider that updates periodically.
    Shared across all metric widgets.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.cpu = 0.0
        self.mem = 0.0
        self.disk = []
        self.gpu = []

        # Start periodic updates
        GLib.timeout_add_seconds(2, self._update)
        self._update()  # Initial update

    def _update(self):
        """Update all metrics"""
        self.cpu = psutil.cpu_percent(interval=0)
        self.mem = psutil.virtual_memory().percent
        self.disk = [psutil.disk_usage("/").percent]

        # GPU via nvtop (optional)
        self._update_gpu_async()

        return True

    def _update_gpu_async(self):
        """Update GPU metrics in background"""
        import subprocess
        import json

        try:
            result = subprocess.run(
                ["nvtop", "-s"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            info = json.loads(result.stdout)
            self.gpu = [
                int(v.get("gpu_util", "0%").strip("%"))
                for v in info
            ]
        except Exception:
            self.gpu = []

    def get_metrics(self):
        """Return current metrics"""
        return (self.cpu, self.mem, self.disk, self.gpu)


# Shared provider instance
shared_provider = MetricsProvider()


class SingularMetric(Box):
    """Single metric display with vertical bar and icon"""

    def __init__(self, metric_id: str, name: str, icon: str, **kwargs):
        super().__init__(
            name=f"ax-metric-{metric_id}",
            orientation="v",
            spacing=8,
            v_align="fill",
            v_expand=True,
            **kwargs,
        )

        self.metric_id = metric_id

        # Vertical scale (progress bar)
        self.scale = Scale(
            name=f"ax-{metric_id}-scale",
            value=0.0,
            orientation="v",
            inverted=True,
            v_align="fill",
            v_expand=True,
        )
        self.scale.set_sensitive(False)  # Not interactive
        self.scale.set_range(0, 1)

        # Icon label
        self.icon_label = Label(
            name=f"ax-{metric_id}-icon",
            label=icon,
        )

        self.add(self.scale)
        self.add(self.icon_label)

        self.set_tooltip_text(f"{icon} {name}")

    def set_value(self, value: float):
        """Set the metric value (0-100)"""
        self.scale.set_value(value / 100.0)


class Metrics(Box):
    """System metrics panel with CPU, RAM, Disk, GPU"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-metrics",
            orientation="h",
            spacing=12,
            h_align="center",
            v_align="fill",
            **kwargs,
        )

        # Create metric displays
        self.cpu = SingularMetric("cpu", "CPU", icons.cpu)
        self.ram = SingularMetric("ram", "RAM", icons.memory)
        self.disk = SingularMetric("disk", "Disk", icons.disk)
        self.gpu = SingularMetric("gpu", "GPU", icons.gpu)

        self.add(self.disk)
        self.add(self.ram)
        self.add(self.cpu)
        self.add(self.gpu)

        # Start update timer
        GLib.timeout_add_seconds(2, self._update_metrics)
        self._update_metrics()  # Initial update

    def _update_metrics(self):
        """Update all metric displays"""
        cpu, mem, disks, gpus = shared_provider.get_metrics()

        self.cpu.set_value(cpu)
        self.ram.set_value(mem)

        if disks:
            self.disk.set_value(disks[0])
            self.disk.set_visible(True)
        else:
            self.disk.set_visible(False)

        if gpus:
            self.gpu.set_value(gpus[0])
            self.gpu.set_visible(True)
        else:
            self.gpu.set_visible(False)

        return True
