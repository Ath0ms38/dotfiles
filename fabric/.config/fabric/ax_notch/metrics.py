"""
System Metrics Widget
Displays CPU, RAM, Disk, GPU usage with labels, percentages, and values
"""

import os
import psutil
import subprocess
import json
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.scale import Scale
from gi.repository import GLib, Gtk
import cairo
import math

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
        self.mem_percent = 0.0
        self.mem_used = 0.0
        self.mem_total = 0.0
        self.disk_percent = 0.0
        self.disk_used = 0.0
        self.disk_total = 0.0
        self.gpu_percent = 0.0
        self.gpu_mem_used = 0.0
        self.gpu_mem_total = 0.0
        self.has_gpu = False
        self.gpu_name = ""  # "nvidia", "intel", or "amd"
        self._nvidia_available = None  # Cache nvidia availability

        # Start periodic updates
        GLib.timeout_add_seconds(2, self._update)
        self._update()  # Initial update

    def _update(self):
        """Update all metrics"""
        # CPU
        self.cpu = psutil.cpu_percent(interval=0)

        # Memory
        mem = psutil.virtual_memory()
        self.mem_percent = mem.percent
        self.mem_used = mem.used / (1024 ** 3)  # GB
        self.mem_total = mem.total / (1024 ** 3)  # GB

        # Disk
        disk = psutil.disk_usage("/")
        self.disk_percent = disk.percent
        self.disk_used = disk.used / (1024 ** 3)  # GB
        self.disk_total = disk.total / (1024 ** 3)  # GB

        # GPU via nvidia-smi (async)
        self._update_gpu_async()

        return True

    def _update_gpu_async(self):
        """Update GPU metrics - try nvidia first, then intel, then amd"""
        # Check nvidia-smi availability (cached)
        if self._nvidia_available is None:
            import shutil
            self._nvidia_available = shutil.which("nvidia-smi") is not None

        if self._nvidia_available:
            self._update_nvidia_gpu()
        else:
            # Try Intel or AMD
            self._update_intel_gpu()

    def _update_nvidia_gpu(self):
        """Update NVIDIA GPU metrics"""
        try:
            proc = subprocess.Popen(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                 "--format=csv,noheader,nounits"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            GLib.timeout_add(100, self._process_nvidia_result, proc)
        except Exception:
            self._nvidia_available = False
            self._update_intel_gpu()

    def _process_nvidia_result(self, proc):
        """Process NVIDIA GPU query result"""
        if proc.poll() is None:
            return True
        try:
            stdout, _ = proc.communicate(timeout=0.1)
            if stdout:
                parts = stdout.strip().split(", ")
                if len(parts) >= 3:
                    self.gpu_percent = float(parts[0])
                    self.gpu_mem_used = float(parts[1]) / 1024  # GB
                    self.gpu_mem_total = float(parts[2]) / 1024  # GB
                    self.has_gpu = True
                    self.gpu_name = "nvidia"
                    return False
        except Exception:
            pass
        # NVIDIA failed, try Intel
        self._nvidia_available = False
        self._update_intel_gpu()
        return False

    def _update_intel_gpu(self):
        """Update Intel GPU metrics via intel_gpu_top or sysfs"""
        try:
            # Try reading from sysfs for Intel GPU frequency/utilization
            # Intel GPUs expose data in /sys/class/drm/card*/
            import glob

            # Find Intel GPU card
            for card_path in glob.glob("/sys/class/drm/card*/device/vendor"):
                try:
                    with open(card_path) as f:
                        vendor = f.read().strip()
                    # Intel vendor ID is 0x8086
                    if vendor == "0x8086":
                        card_dir = os.path.dirname(os.path.dirname(card_path))

                        # Try to get GPU frequency as utilization proxy
                        gt_cur_freq = os.path.join(card_dir, "gt_cur_freq_mhz")
                        gt_max_freq = os.path.join(card_dir, "gt_max_freq_mhz")

                        if os.path.exists(gt_cur_freq) and os.path.exists(gt_max_freq):
                            with open(gt_cur_freq) as f:
                                cur_freq = int(f.read().strip())
                            with open(gt_max_freq) as f:
                                max_freq = int(f.read().strip())

                            # Estimate utilization as percentage of max frequency
                            if max_freq > 0:
                                self.gpu_percent = (cur_freq / max_freq) * 100
                                self.has_gpu = True
                                self.gpu_name = "intel"
                                self.gpu_mem_used = 0  # Intel integrated uses system RAM
                                self.gpu_mem_total = 0
                                return
                except Exception:
                    continue

            # Fallback: try AMD
            self._update_amd_gpu()

        except Exception:
            self._update_amd_gpu()

    def _update_amd_gpu(self):
        """Update AMD GPU metrics via sysfs"""
        try:
            import glob

            for card_path in glob.glob("/sys/class/drm/card*/device/vendor"):
                try:
                    with open(card_path) as f:
                        vendor = f.read().strip()
                    # AMD vendor ID is 0x1002
                    if vendor == "0x1002":
                        card_dir = os.path.dirname(os.path.dirname(card_path))

                        # AMD exposes gpu_busy_percent
                        gpu_busy = os.path.join(card_dir, "gpu_busy_percent")
                        if os.path.exists(gpu_busy):
                            with open(gpu_busy) as f:
                                self.gpu_percent = int(f.read().strip())
                            self.has_gpu = True
                            self.gpu_name = "amd"

                            # Try to get VRAM info
                            vram_used = os.path.join(card_dir, "mem_info_vram_used")
                            vram_total = os.path.join(card_dir, "mem_info_vram_total")
                            if os.path.exists(vram_used) and os.path.exists(vram_total):
                                with open(vram_used) as f:
                                    self.gpu_mem_used = int(f.read().strip()) / (1024**3)
                                with open(vram_total) as f:
                                    self.gpu_mem_total = int(f.read().strip()) / (1024**3)
                            return
                except Exception:
                    continue

            self.has_gpu = False
        except Exception:
            self.has_gpu = False

    def get_metrics(self):
        """Return current metrics as dict"""
        return {
            "cpu": self.cpu,
            "mem_percent": self.mem_percent,
            "mem_used": self.mem_used,
            "mem_total": self.mem_total,
            "disk_percent": self.disk_percent,
            "disk_used": self.disk_used,
            "disk_total": self.disk_total,
            "gpu_percent": self.gpu_percent,
            "gpu_mem_used": self.gpu_mem_used,
            "gpu_mem_total": self.gpu_mem_total,
            "has_gpu": self.has_gpu,
            "gpu_name": self.gpu_name,
        }


# Shared provider instance
shared_provider = MetricsProvider()


class CircularProgress(Gtk.DrawingArea):
    """Circular progress indicator"""

    def __init__(self, size: int = 50, line_width: int = 4, **kwargs):
        super().__init__(**kwargs)
        self.set_size_request(size, size)
        self._size = size
        self._line_width = line_width
        self._value = 0.0

        # Colors
        self._bg_color = (0.2, 0.2, 0.25, 0.5)
        self._fg_color = (0.886, 0.486, 0.757, 1.0)  # Pink accent

        self.connect("draw", self._on_draw)

    def set_value(self, value: float):
        """Set progress value (0-100)"""
        self._value = max(0, min(100, value))
        self.queue_draw()

    def set_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Set the progress color"""
        self._fg_color = (r, g, b, a)
        self.queue_draw()

    def _on_draw(self, widget, cr):
        """Draw the circular progress"""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        size = min(width, height)

        center_x = width / 2
        center_y = height / 2
        radius = (size - self._line_width) / 2

        # Background circle
        cr.set_source_rgba(*self._bg_color)
        cr.set_line_width(self._line_width)
        cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
        cr.stroke()

        # Progress arc
        if self._value > 0:
            cr.set_source_rgba(*self._fg_color)
            cr.set_line_cap(cairo.LineCap.ROUND)
            start_angle = -math.pi / 2
            end_angle = start_angle + (self._value / 100) * 2 * math.pi
            cr.arc(center_x, center_y, radius, start_angle, end_angle)
            cr.stroke()

        return False


class MetricCard(Box):
    """Single metric display card with circular progress, label, and values"""

    def __init__(self, metric_id: str, name: str, icon: str, color: tuple = None, **kwargs):
        super().__init__(
            name=f"ax-metric-{metric_id}",
            orientation="v",
            spacing=4,
            h_align="center",
            v_align="center",
            **kwargs,
        )

        self.metric_id = metric_id
        self.metric_name = name

        # Circular progress
        self.progress = CircularProgress(size=56, line_width=5)
        if color:
            self.progress.set_color(*color)
        self.progress.set_name(f"ax-metric-{metric_id}-progress")

        # Icon inside circle (overlay)
        self.icon_label = Label(
            name=f"ax-metric-{metric_id}-icon",
            label=icon,
        )

        # Progress container with centered icon
        progress_container = Gtk.Overlay()
        progress_container.add(self.progress)
        progress_container.add_overlay(self.icon_label)
        self.icon_label.set_halign(Gtk.Align.CENTER)
        self.icon_label.set_valign(Gtk.Align.CENTER)

        # Name label
        self.name_label = Label(
            name=f"ax-metric-{metric_id}-name",
            label=name,
        )

        # Percentage label
        self.percent_label = Label(
            name=f"ax-metric-{metric_id}-percent",
            label="0%",
        )

        # Value label (e.g., "8.2 / 16 GB")
        self.value_label = Label(
            name=f"ax-metric-{metric_id}-value",
            label="",
        )

        self.add(progress_container)
        self.add(self.name_label)
        self.add(self.percent_label)
        self.add(self.value_label)

    def set_value(self, percent: float, used: float = None, total: float = None, unit: str = ""):
        """Update the metric display"""
        self.progress.set_value(percent)
        self.percent_label.set_label(f"{int(percent)}%")

        if used is not None and total is not None:
            self.value_label.set_label(f"{used:.1f} / {total:.1f} {unit}")
            self.value_label.set_visible(True)
        else:
            self.value_label.set_visible(False)


class Metrics(Box):
    """System metrics panel with CPU, RAM, Disk, GPU cards"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-metrics",
            orientation="h",
            spacing=16,
            h_align="center",
            v_align="center",
            **kwargs,
        )

        # Colors for each metric (RGBA)
        colors = {
            "cpu": (0.4, 0.8, 0.95, 1.0),      # Cyan
            "ram": (0.886, 0.486, 0.757, 1.0),  # Pink
            "disk": (0.6, 0.8, 0.4, 1.0),       # Green
            "gpu": (0.95, 0.7, 0.3, 1.0),       # Orange
        }

        # Create metric cards
        self.cpu = MetricCard("cpu", "CPU", icons.cpu, color=colors["cpu"])
        self.ram = MetricCard("ram", "RAM", icons.memory, color=colors["ram"])
        self.disk = MetricCard("disk", "Storage", icons.disk, color=colors["disk"])
        self.gpu = MetricCard("gpu", "GPU", icons.gpu, color=colors["gpu"])

        self.add(self.cpu)
        self.add(self.ram)
        self.add(self.disk)
        self.add(self.gpu)

        # Start update timer
        GLib.timeout_add_seconds(2, self._update_metrics)
        self._update_metrics()  # Initial update

    def _update_metrics(self):
        """Update all metric displays"""
        metrics = shared_provider.get_metrics()

        # CPU
        self.cpu.set_value(metrics["cpu"])

        # RAM
        self.ram.set_value(
            metrics["mem_percent"],
            metrics["mem_used"],
            metrics["mem_total"],
            "GB"
        )

        # Disk
        self.disk.set_value(
            metrics["disk_percent"],
            metrics["disk_used"],
            metrics["disk_total"],
            "GB"
        )

        # GPU
        if metrics["has_gpu"]:
            self.gpu.set_value(
                metrics["gpu_percent"],
                metrics["gpu_mem_used"] if metrics["gpu_mem_total"] > 0 else None,
                metrics["gpu_mem_total"] if metrics["gpu_mem_total"] > 0 else None,
                "GB"
            )
            self.gpu.set_visible(True)
        else:
            self.gpu.set_visible(False)

        return True
