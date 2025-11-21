"""
Network & Bluetooth Management Widget
Controls WiFi and Bluetooth connections
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.wayland import WaylandWindow
from fabric.bluetooth.service import BluetoothClient
import subprocess


class WiFiNetworkItem(Box):
    """A WiFi network list item"""

    def __init__(self, ssid: str, signal: int, security: str, in_use: bool = False, **kwargs):
        super().__init__(
            orientation="h",
            spacing=8,
            name="wifi-item",
            **kwargs
        )

        self.ssid = ssid
        self.signal = signal
        self.security = security
        self.in_use = in_use

        # Signal strength icon
        if signal >= 75:
            signal_icon = "󰤨"
        elif signal >= 50:
            signal_icon = "󰤥"
        elif signal >= 25:
            signal_icon = "󰤢"
        else:
            signal_icon = "󰤟"

        # Security icon
        security_icon = "󰌾" if security != "--" else ""

        # In use indicator
        in_use_indicator = "✓ " if in_use else "  "

        # Network info
        info_label = Label(
            label=f"{in_use_indicator}{signal_icon} {ssid} {signal}% {security_icon}",
            h_expand=True,
            h_align="start"
        )

        # Connect button
        connect_btn = Button(
            label="Disconnect" if in_use else "Connect",
            on_clicked=lambda *_: self.toggle_connection()
        )

        self.add(info_label)
        self.add(connect_btn)

    def toggle_connection(self):
        """Toggle WiFi connection"""
        try:
            if self.in_use:
                subprocess.run(["nmcli", "connection", "down", self.ssid], check=False)
            else:
                subprocess.run(["nmcli", "device", "wifi", "connect", self.ssid], check=False)
        except Exception as e:
            print(f"Error toggling WiFi connection: {e}")


class BluetoothDeviceItem(Box):
    """A Bluetooth device list item"""

    def __init__(self, device, **kwargs):
        super().__init__(
            orientation="h",
            spacing=8,
            name="bluetooth-item",
            **kwargs
        )

        self.device = device

        # Device info
        icon = device.icon_name or "bluetooth"
        name = device.name or device.address
        status = "Connected" if device.connected else "Paired" if device.paired else "Available"

        info_label = Label(
            label=f"󰂯 {name} ({status})",
            h_expand=True,
            h_align="start"
        )

        # Connect button
        if device.paired:
            btn_label = "Disconnect" if device.connected else "Connect"
            connect_btn = Button(
                label=btn_label,
                on_clicked=lambda *_: device.connect_device(not device.connected)
            )
        else:
            connect_btn = Button(
                label="Pair",
                on_clicked=lambda *_: print("Pairing not yet implemented")
            )

        self.add(info_label)
        self.add(connect_btn)

        # Listen for device changes
        device.connect("changed", self.on_device_changed)

    def on_device_changed(self, device):
        """Handle device property changes"""
        # Rebuild the item when device state changes
        # For simplicity, we'll just update in the parent widget


class NetworkWidget(WaylandWindow):
    """Network & Bluetooth management popup widget"""

    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="top right",
            margin="50px 20px 0px 0px",
            keyboard_mode="on-demand",
            name="network-widget",
            visible=False,
            **kwargs
        )

        # Initialize Bluetooth service
        try:
            self.bluetooth = BluetoothClient()
            self.bluetooth.connect("device-added", lambda *_: self.rebuild_content())
            self.bluetooth.connect("device-removed", lambda *_: self.rebuild_content())
            self.bluetooth.connect("changed", lambda *_: self.rebuild_content())
        except Exception as e:
            print(f"Error initializing Bluetooth: {e}")
            self.bluetooth = None

        # Build widget
        self.children = self.build_content()

    def build_content(self):
        """Build the widget content"""
        content = Box(
            orientation="v",
            spacing=16,
            name="network-content",
            children=[
                Label(
                    label="󰀂 Network & Bluetooth",
                    name="network-title",
                    style="font-size: 16px; font-weight: bold;"
                ),
                self.build_wifi_section(),
                self.build_bluetooth_section(),
            ]
        )

        return ScrolledWindow(
            min_content_size=(450, 100),
            max_content_size=(450, 600),
            child=content
        )

    def build_wifi_section(self):
        """Build WiFi control section"""
        children = [
            Box(
                orientation="h",
                spacing=8,
                children=[
                    Label(
                        label="WiFi",
                        name="section-title",
                        style="font-size: 14px; font-weight: bold;",
                        h_expand=True,
                        h_align="start"
                    ),
                    Button(
                        label="Refresh",
                        on_clicked=lambda *_: self.rebuild_content()
                    ),
                ]
            )
        ]

        # Get WiFi networks
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
                capture_output=True,
                text=True,
                check=True
            )

            networks = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        in_use = parts[0] == '*'
                        ssid = parts[1]
                        signal = int(parts[2]) if parts[2].isdigit() else 0
                        security = parts[3] if parts[3] else "--"

                        if ssid:  # Skip hidden networks
                            networks.append(
                                WiFiNetworkItem(ssid, signal, security, in_use)
                            )

            if networks:
                children.extend(networks[:10])  # Limit to 10 networks
            else:
                children.append(
                    Label(
                        label="No WiFi networks found",
                        name="empty-message",
                        style="opacity: 0.7; font-style: italic;"
                    )
                )

        except Exception as e:
            children.append(
                Label(
                    label=f"Error loading WiFi networks: {e}",
                    name="error-message",
                    style="color: #ff6b6b; font-style: italic;"
                )
            )

        return Box(
            orientation="v",
            spacing=8,
            name="wifi-section",
            children=children
        )

    def build_bluetooth_section(self):
        """Build Bluetooth control section"""
        children = [
            Box(
                orientation="h",
                spacing=8,
                children=[
                    Label(
                        label="Bluetooth",
                        name="section-title",
                        style="font-size: 14px; font-weight: bold;",
                        h_expand=True,
                        h_align="start"
                    ),
                    Button(
                        label="Scan" if self.bluetooth and not self.bluetooth.scanning else "Stop",
                        on_clicked=lambda *_: self.bluetooth.toggle_scan() if self.bluetooth else None
                    ) if self.bluetooth else Label(label=""),
                    Button(
                        label="Power Off" if self.bluetooth and self.bluetooth.powered else "Power On",
                        on_clicked=lambda *_: self.bluetooth.toggle_power() if self.bluetooth else None
                    ) if self.bluetooth else Label(label=""),
                ]
            )
        ]

        if self.bluetooth:
            # Add Bluetooth devices
            if self.bluetooth.devices:
                for device in self.bluetooth.devices[:10]:  # Limit to 10 devices
                    children.append(BluetoothDeviceItem(device))
            else:
                children.append(
                    Label(
                        label="No Bluetooth devices found" + (" - Scanning..." if self.bluetooth.scanning else ""),
                        name="empty-message",
                        style="opacity: 0.7; font-style: italic;"
                    )
                )
        else:
            children.append(
                Label(
                    label="Bluetooth service unavailable",
                    name="error-message",
                    style="color: #ff6b6b; font-style: italic;"
                )
            )

        return Box(
            orientation="v",
            spacing=8,
            name="bluetooth-section",
            children=children
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
network_widget = None


def get_network_widget():
    """Get or create the network widget singleton"""
    global network_widget
    if network_widget is None:
        network_widget = NetworkWidget()
    return network_widget
