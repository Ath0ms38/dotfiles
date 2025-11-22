"""
Audio Management Widget
Comprehensive audio control with:
- Master volume controls (output/input)
- Audio output device selection
- Microphone input device selection
- Per-window application audio control
- Mute controls for all devices
"""

import subprocess
import json
import re
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scale import Scale
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.separator import Separator
from fabric.widgets.revealer import Revealer
from gi.repository import GLib, Gtk
from .base_popup import BasePopup

# Try to import Hyprland for window title matching
try:
    from fabric.hyprland.service import Hyprland
    HYPRLAND_AVAILABLE = True
except ImportError:
    HYPRLAND_AVAILABLE = False


class AudioDevice:
    """Represents an audio input/output device"""

    def __init__(self, name, description, index, is_default=False):
        self.name = name
        self.description = description
        self.index = index
        self.is_default = is_default


class WindowAudioStream:
    """Represents a per-window audio stream from PulseAudio/PipeWire"""

    def __init__(self, sink_input_id, app_name, app_binary, pid, volume, muted, window_title=None):
        self.sink_input_id = sink_input_id
        self.app_name = app_name
        self.app_binary = app_binary
        self.pid = pid
        self.volume = volume  # 0-100
        self.muted = muted
        self.window_title = window_title or app_name

    def __eq__(self, other):
        return isinstance(other, WindowAudioStream) and self.sink_input_id == other.sink_input_id

    def __hash__(self):
        return hash(self.sink_input_id)

    @property
    def display_name(self):
        """Get display name for this stream"""
        if self.window_title and self.window_title != self.app_name:
            return f"{self.app_name} - {self.window_title}"
        return self.app_name

    @property
    def icon(self):
        """Get Nerd Font icon for this application"""
        binary_lower = self.app_binary.lower()
        name_lower = self.app_name.lower()

        if "firefox" in binary_lower or "firefox" in name_lower:
            return "󰈹"
        elif "chrome" in binary_lower or "chromium" in binary_lower:
            return "󰊯"
        elif "discord" in binary_lower or "discord" in name_lower:
            return "󰙯"
        elif "spotify" in binary_lower or "spotify" in name_lower:
            return "󰓇"
        elif "vlc" in binary_lower:
            return "󰕼"
        elif "mpv" in binary_lower:
            return "󰐹"
        elif "music" in name_lower or "audio" in name_lower:
            return "󰝚"
        else:
            return "󰣞"


class PulseAudioManager:
    """Manages PulseAudio/PipeWire audio streams with comprehensive controls"""

    def __init__(self):
        self.hyprland = Hyprland() if HYPRLAND_AVAILABLE else None

    def get_window_title_for_pid(self, pid):
        """Get window title for a given PID using Hyprland"""
        if not self.hyprland:
            return None

        try:
            result = Hyprland.send_command("clients")
            if result and result.is_ok:
                clients = json.loads(result.reply)
                for client in clients:
                    if client.get("pid") == pid:
                        return client.get("title", None)
        except Exception:
            pass
        return None

    def get_sinks(self):
        """Get all audio output devices (sinks)"""
        devices = []
        try:
            result = subprocess.run(
                ["pactl", "list", "sinks"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return devices

            current_device = {}
            for line in result.stdout.split("\n"):
                line_stripped = line.strip()

                if line.startswith("Sink #"):
                    if current_device:
                        devices.append(self._create_device_from_data(current_device))
                    match = re.search(r"Sink #(\d+)", line)
                    current_device = {"index": int(match.group(1)) if match else 0}

                elif ":" in line_stripped:
                    key, value = line_stripped.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "Name":
                        current_device["name"] = value
                    elif key == "Description":
                        current_device["description"] = value
                    elif line_stripped.startswith("* index:"):
                        # Default sink marker
                        current_device["is_default"] = True

            if current_device:
                devices.append(self._create_device_from_data(current_device))

        except Exception as e:
            print(f"Error getting sinks: {e}")

        return devices

    def get_sources(self):
        """Get all audio input devices (sources/microphones)"""
        devices = []
        try:
            result = subprocess.run(
                ["pactl", "list", "sources"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return devices

            current_device = {}
            for line in result.stdout.split("\n"):
                line_stripped = line.strip()

                if line.startswith("Source #"):
                    if current_device:
                        # Filter out monitor sources (those are for recording output)
                        if not current_device.get("name", "").endswith(".monitor"):
                            devices.append(self._create_device_from_data(current_device))
                    match = re.search(r"Source #(\d+)", line)
                    current_device = {"index": int(match.group(1)) if match else 0}

                elif ":" in line_stripped:
                    key, value = line_stripped.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "Name":
                        current_device["name"] = value
                    elif key == "Description":
                        current_device["description"] = value
                    elif line_stripped.startswith("* index:"):
                        current_device["is_default"] = True

            if current_device:
                if not current_device.get("name", "").endswith(".monitor"):
                    devices.append(self._create_device_from_data(current_device))

        except Exception as e:
            print(f"Error getting sources: {e}")

        return devices

    def _create_device_from_data(self, data):
        """Create AudioDevice from parsed data"""
        return AudioDevice(
            name=data.get("name", "unknown"),
            description=data.get("description", "Unknown Device"),
            index=data.get("index", 0),
            is_default=data.get("is_default", False)
        )

    def set_default_sink(self, sink_name):
        """Set default output device"""
        try:
            subprocess.run(
                ["pactl", "set-default-sink", sink_name],
                timeout=1,
                check=False
            )
        except Exception as e:
            print(f"Error setting default sink: {e}")

    def set_default_source(self, source_name):
        """Set default input device"""
        try:
            subprocess.run(
                ["pactl", "set-default-source", source_name],
                timeout=1,
                check=False
            )
        except Exception as e:
            print(f"Error setting default source: {e}")

    def get_sink_inputs(self):
        """Get all audio sink inputs (playing audio streams)"""
        streams = []
        try:
            result = subprocess.run(
                ["pactl", "list", "sink-inputs"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return streams

            current_stream = {}
            in_properties = False

            for line in result.stdout.split("\n"):
                # Check for new sink input
                if line.startswith("Sink Input #"):
                    if current_stream:
                        streams.append(self._create_stream_from_data(current_stream))
                    match = re.search(r"Sink Input #(\d+)", line)
                    current_stream = {"id": int(match.group(1)) if match else 0}
                    in_properties = False
                    continue

                # Check for properties section
                if line.strip() == "Properties:":
                    in_properties = True
                    continue

                # Parse top-level properties (Volume, Mute)
                if not in_properties and ":" in line and not line.startswith("\t\t"):
                    stripped = line.strip()
                    if ":" in stripped:
                        key, value = stripped.split(":", 1)
                        key = key.strip()
                        value = value.strip()

                        if key == "Volume":
                            volume_match = re.search(r"(\d+)%", value)
                            if volume_match:
                                current_stream["volume"] = int(volume_match.group(1))
                        elif key == "Mute":
                            current_stream["muted"] = value.lower() == "yes"

                # Parse properties under Properties: section
                if in_properties and "=" in line:
                    # Properties are like: application.name = "Firefox"
                    match = re.match(r'\s*([^\s=]+)\s*=\s*"?([^"]*)"?', line)
                    if match:
                        key = match.group(1)
                        value = match.group(2)

                        if key == "application.name":
                            current_stream["app_name"] = value
                        elif key == "application.process.binary":
                            current_stream["app_binary"] = value
                        elif key == "application.process.id":
                            try:
                                current_stream["pid"] = int(value)
                            except (ValueError, TypeError):
                                current_stream["pid"] = 0
                        elif key == "media.name":
                            # Use media.name as a fallback for window title
                            if "media_name" not in current_stream:
                                current_stream["media_name"] = value

            if current_stream:
                streams.append(self._create_stream_from_data(current_stream))

        except Exception as e:
            print(f"Error getting sink inputs: {e}")

        return streams

    def _create_stream_from_data(self, data):
        """Create WindowAudioStream from parsed data"""
        sink_id = data.get("id", 0)
        app_name = data.get("app_name", "Unknown")
        app_binary = data.get("app_binary", "unknown")
        pid = data.get("pid", 0)
        volume = data.get("volume", 100)
        muted = data.get("muted", False)

        # Try to get window title from Hyprland first
        window_title = self.get_window_title_for_pid(pid) if pid else None

        # If no window title from Hyprland, use media.name from PulseAudio
        if not window_title:
            window_title = data.get("media_name", None)

        return WindowAudioStream(
            sink_input_id=sink_id,
            app_name=app_name,
            app_binary=app_binary,
            pid=pid,
            volume=volume,
            muted=muted,
            window_title=window_title
        )

    def set_volume(self, sink_input_id, volume):
        """Set volume for a sink input (0-100)"""
        try:
            subprocess.run(
                ["pactl", "set-sink-input-volume", str(sink_input_id), f"{volume}%"],
                timeout=1,
                check=False
            )
        except Exception as e:
            print(f"Error setting volume: {e}")

    def set_mute(self, sink_input_id, muted):
        """Set mute state for a sink input"""
        try:
            mute_arg = "1" if muted else "0"
            subprocess.run(
                ["pactl", "set-sink-input-mute", str(sink_input_id), mute_arg],
                timeout=1,
                check=False
            )
        except Exception as e:
            print(f"Error setting mute: {e}")

    def get_default_sink_volume(self):
        """Get default sink (speaker) volume"""
        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                match = re.search(r"(\d+)%", result.stdout)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        return 50

    def get_default_sink_mute(self):
        """Get default sink mute state"""
        try:
            result = subprocess.run(
                ["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return "yes" in result.stdout.lower()
        except Exception:
            pass
        return False

    def set_default_sink_volume(self, volume):
        """Set default sink (speaker) volume (0-100)"""
        try:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"],
                timeout=1,
                check=False
            )
        except Exception as e:
            print(f"Error setting sink volume: {e}")

    def set_default_sink_mute(self, muted):
        """Set default sink mute state"""
        try:
            mute_arg = "1" if muted else "0"
            subprocess.run(
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", mute_arg],
                timeout=1,
                check=False
            )
        except Exception as e:
            print(f"Error setting sink mute: {e}")

    def get_default_source_volume(self):
        """Get default source (microphone) volume"""
        try:
            result = subprocess.run(
                ["pactl", "get-source-volume", "@DEFAULT_SOURCE@"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                match = re.search(r"(\d+)%", result.stdout)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        return 50

    def get_default_source_mute(self):
        """Get default source mute state"""
        try:
            result = subprocess.run(
                ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return "yes" in result.stdout.lower()
        except Exception:
            pass
        return False

    def set_default_source_volume(self, volume):
        """Set default source (microphone) volume (0-100)"""
        try:
            subprocess.run(
                ["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{volume}%"],
                timeout=1,
                check=False
            )
        except Exception as e:
            print(f"Error setting source volume: {e}")

    def set_default_source_mute(self, muted):
        """Set default source mute state"""
        try:
            mute_arg = "1" if muted else "0"
            subprocess.run(
                ["pactl", "set-source-mute", "@DEFAULT_SOURCE@", mute_arg],
                timeout=1,
                check=False
            )
        except Exception as e:
            print(f"Error setting source mute: {e}")


class DeviceSelector(Box):
    """Device selection dropdown for audio output/input"""

    def __init__(self, devices, device_type, pa_manager, **kwargs):
        super().__init__(
            orientation="v",
            spacing=4,
            name="device-selector",
            **kwargs
        )

        self.devices = devices
        self.device_type = device_type  # "sink" or "source"
        self.pa_manager = pa_manager

        # Find default device
        default_device = next((d for d in devices if d.is_default), devices[0] if devices else None)

        if default_device:
            # Create buttons for each device
            for device in devices:
                is_active = device.is_default
                button = Button(
                    label=f"{'●' if is_active else '○'} {device.description}",
                    name="device-button",
                    h_align="start",
                    on_clicked=lambda b, d=device: self.select_device(d)
                )
                if is_active:
                    button.add_style_class("active-device")
                self.add(button)

    def select_device(self, device):
        """Select a device as default"""
        if self.device_type == "sink":
            self.pa_manager.set_default_sink(device.name)
        else:
            self.pa_manager.set_default_source(device.name)

        # Update button labels
        for child in self.get_children():
            if isinstance(child, Button):
                # Extract device description from label
                label_text = child.get_label()
                if label_text:
                    desc = label_text.split(" ", 1)[1] if " " in label_text else label_text
                    is_selected = desc == device.description
                    child.set_label(f"{'●' if is_selected else '○'} {desc}")
                    if is_selected:
                        child.add_style_class("active-device")
                    else:
                        child.remove_style_class("active-device")


class WindowAudioControl(Box):
    """Control widget for a single window's audio stream"""

    def __init__(self, stream, pa_manager, **kwargs):
        super().__init__(
            orientation="v",
            spacing=4,
            name="window-audio-control",
            **kwargs
        )

        self.stream = stream
        self.pa_manager = pa_manager
        self.updating = False

        # Header with icon, name, and mute button
        self.name_label = Label(
            label=f"{stream.icon} {stream.display_name}",
            name="stream-name",
            h_align="start",
            h_expand=True
        )

        self.volume_label = Label(
            label=f"{stream.volume}%",
            name="volume-percent"
        )

        self.mute_button = Button(
            label="󰝟" if stream.muted else "󰕾",
            name="mute-button",
            on_clicked=self.toggle_mute
        )

        header = Box(
            orientation="h",
            spacing=8,
            children=[
                self.name_label,
                self.volume_label,
                self.mute_button,
            ]
        )

        # Volume slider
        self.volume_scale = Scale(
            orientation="h",
            min_value=0.0,
            max_value=100.0,
            value=float(stream.volume),
            draw_value=False,
            h_expand=True,
            name="volume-slider"
        )
        self.volume_scale.connect("value-changed", self.on_volume_changed)

        self.add(header)
        self.add(self.volume_scale)

    def on_volume_changed(self, scale):
        """Handle volume slider changes"""
        if self.updating:
            return

        volume = int(scale.get_value())
        self.volume_label.set_label(f"{volume}%")
        self.pa_manager.set_volume(self.stream.sink_input_id, volume)

    def toggle_mute(self, *args):
        """Toggle mute state"""
        new_muted = not self.stream.muted
        self.stream.muted = new_muted
        self.mute_button.set_label("󰝟" if new_muted else "󰕾")
        self.pa_manager.set_mute(self.stream.sink_input_id, new_muted)

    def update_from_stream(self, stream):
        """Update UI from stream data"""
        self.updating = True
        self.stream = stream
        self.name_label.set_label(f"{stream.icon} {stream.display_name}")
        self.volume_label.set_label(f"{stream.volume}%")
        self.volume_scale.set_value(float(stream.volume))
        self.mute_button.set_label("󰝟" if stream.muted else "󰕾")
        self.updating = False


class ApplicationAudioGroup(Box):
    """Collapsible group of audio controls for windows of the same application"""

    def __init__(self, app_name, app_icon, streams, pa_manager, **kwargs):
        super().__init__(
            orientation="v",
            spacing=4,
            name="app-audio-group",
            **kwargs
        )

        self.app_name = app_name
        self.app_icon = app_icon
        self.pa_manager = pa_manager
        self.stream_controls = {}
        self.is_expanded = False

        # Header button to expand/collapse
        window_count = len(streams)
        self.header_button = Button(
            label=f"{app_icon} {app_name} ({window_count} window{'s' if window_count != 1 else ''})",
            name="app-group-header",
            h_align="start",
            on_clicked=self.toggle_expand
        )

        # Revealer for window controls
        self.revealer = Revealer(
            transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
            transition_duration=200,
            reveal_child=False
        )

        # Container for individual window controls
        self.windows_container = Box(
            orientation="v",
            spacing=4,
            name="windows-container"
        )

        self.revealer.add(self.windows_container)

        self.add(self.header_button)
        self.add(self.revealer)

        # Add all stream controls
        for stream in streams:
            control = WindowAudioControl(stream, pa_manager)
            self.stream_controls[stream.sink_input_id] = control
            self.windows_container.add(control)

    def toggle_expand(self, *args):
        """Toggle expanded state"""
        self.is_expanded = not self.is_expanded
        self.revealer.set_reveal_child(self.is_expanded)

        # Update button label with expand indicator
        window_count = len(self.stream_controls)
        expand_icon = "▼" if self.is_expanded else "▶"
        self.header_button.set_label(
            f"{expand_icon} {self.app_icon} {self.app_name} ({window_count} window{'s' if window_count != 1 else ''})"
        )

    def update_streams(self, streams):
        """Update the streams in this group"""
        current_ids = {s.sink_input_id for s in streams}
        existing_ids = set(self.stream_controls.keys())

        # Remove streams that no longer exist
        for stream_id in (existing_ids - current_ids):
            control = self.stream_controls.pop(stream_id)
            self.windows_container.remove(control)

        # Add new streams
        for stream in streams:
            if stream.sink_input_id not in self.stream_controls:
                control = WindowAudioControl(stream, self.pa_manager)
                self.stream_controls[stream.sink_input_id] = control
                self.windows_container.add(control)
            else:
                # Update existing control
                self.stream_controls[stream.sink_input_id].update_from_stream(stream)

        # Update header label with new count
        window_count = len(self.stream_controls)
        expand_icon = "▼" if self.is_expanded else "▶"
        self.header_button.set_label(
            f"{expand_icon} {self.app_icon} {self.app_name} ({window_count} window{'s' if window_count != 1 else ''})"
        )

        self.windows_container.show_all()


class MasterVolumeControl(Box):
    """Master volume control for system output/input with mute button"""

    def __init__(self, name, pa_manager, is_source=False, **kwargs):
        super().__init__(
            orientation="v",
            spacing=4,
            name="master-volume-control",
            **kwargs
        )

        self.pa_manager = pa_manager
        self.is_source = is_source
        self.updating = False

        # Get initial volume and mute state
        if is_source:
            initial_volume = pa_manager.get_default_source_volume()
            initial_muted = pa_manager.get_default_source_mute()
            icon = "󰍬"
        else:
            initial_volume = pa_manager.get_default_sink_volume()
            initial_muted = pa_manager.get_default_sink_mute()
            icon = "󰓃"

        # Header
        self.name_label = Label(
            label=f"{icon} {name}",
            name="master-name",
            h_align="start",
            h_expand=True,
            style="font-weight: bold;"
        )

        self.volume_label = Label(
            label=f"{initial_volume}%",
            name="master-volume-percent"
        )

        self.mute_button = Button(
            label="󰝟" if initial_muted else "󰕾",
            name="master-mute-button",
            on_clicked=self.toggle_mute
        )

        header = Box(
            orientation="h",
            spacing=8,
            children=[self.name_label, self.volume_label, self.mute_button]
        )

        # Volume slider
        self.volume_scale = Scale(
            orientation="h",
            min_value=0.0,
            max_value=100.0,
            value=float(initial_volume),
            draw_value=False,
            h_expand=True,
            name="master-volume-slider"
        )
        self.volume_scale.connect("value-changed", self.on_volume_changed)

        self.add(header)
        self.add(self.volume_scale)

    def on_volume_changed(self, scale):
        """Handle volume changes"""
        if self.updating:
            return

        volume = int(scale.get_value())
        self.volume_label.set_label(f"{volume}%")

        if self.is_source:
            self.pa_manager.set_default_source_volume(volume)
        else:
            self.pa_manager.set_default_sink_volume(volume)

    def toggle_mute(self, *args):
        """Toggle mute state"""
        if self.is_source:
            current_muted = self.pa_manager.get_default_source_mute()
            new_muted = not current_muted
            self.pa_manager.set_default_source_mute(new_muted)
        else:
            current_muted = self.pa_manager.get_default_sink_mute()
            new_muted = not current_muted
            self.pa_manager.set_default_sink_mute(new_muted)

        self.mute_button.set_label("󰝟" if new_muted else "󰕾")


class AudioWidget(BasePopup):
    """Comprehensive audio management popup"""

    def __init__(self, **kwargs):
        self.pa_manager = PulseAudioManager()
        self.app_groups = {}  # Map app_name to ApplicationAudioGroup
        self.update_timeout_id = None

        super().__init__(
            name="audio-widget",
            anchor="top right",
            margin="50px 20px 0px 0px",
            width=500,
            **kwargs
        )

    def build_content(self):
        """Build the comprehensive audio widget content"""
        # Master volume controls
        master_section = Box(
            orientation="v",
            spacing=12,
            children=[
                Label(
                    label="󰓃 Master Volume",
                    name="section-title",
                    h_align="start",
                    style="font-size: 14px; font-weight: bold; margin-bottom: 4px;"
                ),
                MasterVolumeControl("Output (Speakers)", self.pa_manager, is_source=False),
                MasterVolumeControl("Input (Microphone)", self.pa_manager, is_source=True),
            ]
        )

        # Output device selection
        output_devices = self.pa_manager.get_sinks()
        self.output_selector_container = Box(
            orientation="v",
            spacing=8,
            name="output-selector-container"
        )

        output_section = Box(
            orientation="v",
            spacing=8,
            children=[
                Separator(orientation="h"),
                Label(
                    label="󰋋 Audio Output Device",
                    name="section-title",
                    h_align="start",
                    style="font-size: 14px; font-weight: bold; margin-bottom: 4px;"
                ),
                DeviceSelector(output_devices, "sink", self.pa_manager) if output_devices else Label(label="No output devices found", style="opacity: 0.7;"),
            ]
        )

        # Input device selection
        input_devices = self.pa_manager.get_sources()
        input_section = Box(
            orientation="v",
            spacing=8,
            children=[
                Separator(orientation="h"),
                Label(
                    label="󰍬 Audio Input Device",
                    name="section-title",
                    h_align="start",
                    style="font-size: 14px; font-weight: bold; margin-bottom: 4px;"
                ),
                DeviceSelector(input_devices, "source", self.pa_manager) if input_devices else Label(label="No input devices found", style="opacity: 0.7;"),
            ]
        )

        # Per-window streams section
        self.streams_container = Box(
            orientation="v",
            spacing=8,
            name="streams-container"
        )

        streams_section = Box(
            orientation="v",
            spacing=12,
            children=[
                Separator(orientation="h"),
                Label(
                    label="󰣞 Per-Window Audio",
                    name="section-title",
                    h_align="start",
                    style="font-size: 14px; font-weight: bold; margin-bottom: 4px;"
                ),
                self.streams_container,
            ]
        )

        # Main content
        content = Box(
            orientation="v",
            spacing=16,
            name="audio-content",
            children=[
                Label(
                    label="󰕾 Audio Control",
                    name="audio-title",
                    style="font-size: 16px; font-weight: bold;"
                ),
                master_section,
                output_section,
                input_section,
                streams_section,
            ]
        )

        # Return content directly without scrolling
        return content

    def on_open(self):
        """Called when widget opens - start updates"""
        self.update_streams()
        if not self.update_timeout_id:
            self.update_timeout_id = GLib.timeout_add(500, self.update_streams)

    def close(self):
        """Override close to stop updates"""
        if self.update_timeout_id:
            GLib.source_remove(self.update_timeout_id)
            self.update_timeout_id = None
        super().close()

    def close_immediate(self):
        """Override close_immediate to stop updates"""
        if self.update_timeout_id:
            GLib.source_remove(self.update_timeout_id)
            self.update_timeout_id = None
        super().close_immediate()

    def update_streams(self):
        """Update window audio streams grouped by application"""
        streams = self.pa_manager.get_sink_inputs()

        # Group streams by application name
        streams_by_app = {}
        for stream in streams:
            app_name = stream.app_name
            if app_name not in streams_by_app:
                streams_by_app[app_name] = []
            streams_by_app[app_name].append(stream)

        current_apps = set(streams_by_app.keys())
        existing_apps = set(self.app_groups.keys())

        # Remove app groups that no longer have streams
        for app_name in (existing_apps - current_apps):
            group = self.app_groups.pop(app_name)
            self.streams_container.remove(group)

        # Add new app groups
        for app_name in (current_apps - existing_apps):
            app_streams = streams_by_app[app_name]
            # Get icon from first stream
            app_icon = app_streams[0].icon if app_streams else "󰣞"
            group = ApplicationAudioGroup(app_name, app_icon, app_streams, self.pa_manager)
            self.app_groups[app_name] = group
            self.streams_container.add(group)

        # Update existing app groups
        for app_name in (current_apps & existing_apps):
            app_streams = streams_by_app[app_name]
            group = self.app_groups[app_name]
            group.update_streams(app_streams)

        # Show empty message if no streams
        if not streams:
            if not any(isinstance(child, Label) and child.get_name() == "empty-message"
                      for child in self.streams_container.get_children()):
                empty_label = Label(
                    label="No applications playing audio",
                    name="empty-message",
                    style="opacity: 0.7; font-style: italic; margin: 12px 0;"
                )
                self.streams_container.add(empty_label)
        else:
            # Remove empty message if it exists
            for child in self.streams_container.get_children():
                if isinstance(child, Label) and child.get_name() == "empty-message":
                    self.streams_container.remove(child)

        self.streams_container.show_all()
        return self.get_visible()


# Singleton instance
audio_widget = None


def get_audio_widget():
    """Get or create the audio widget singleton"""
    global audio_widget
    if audio_widget is None:
        audio_widget = AudioWidget()
    return audio_widget
