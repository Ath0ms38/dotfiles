"""
Network & WiFi Management Widget
Comprehensive network control with:
- WiFi toggle and scanning with password support
- Access point list with signal strength and security info
- Ethernet connection information
- Real-time connection status with speed/frequency
- Progressive content reveal animation
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.image import Image
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.entry import Entry
from gi.repository import GLib, Gtk
from .base_popup import BasePopup
from services.network import NetworkClient


class PasswordEntryRow(Box):
    """Inline password entry that appears below the access point"""

    def __init__(self, ssid: str, on_connect_callback, on_cancel_callback, **kwargs):
        super().__init__(
            orientation="v",
            spacing=8,
            name="password-entry-row",
            **kwargs
        )
        self.ssid = ssid
        self.on_connect_callback = on_connect_callback
        self.on_cancel_callback = on_cancel_callback

        # Password entry
        self.password_entry = Entry(
            placeholder=f"Password for {ssid}...",
            h_expand=True,
            visibility=False,  # Hide password
            on_activate=self._on_connect
        )

        # Buttons
        connect_btn = Button(
            label="Connect",
            name="password-connect-btn",
            on_clicked=self._on_connect
        )

        cancel_btn = Button(
            label="Cancel",
            name="password-cancel-btn",
            on_clicked=lambda *_: self.on_cancel_callback()
        )

        # Layout
        button_box = Box(
            orientation="h",
            spacing=8,
            h_align="end",
            children=[cancel_btn, connect_btn]
        )

        self.add(self.password_entry)
        self.add(button_box)

    def _on_connect(self, *args):
        password = self.password_entry.get_text()
        if password:
            self.on_connect_callback(password)
            self.password_entry.set_text("")  # Clear password

    def grab_entry_focus(self):
        self.password_entry.grab_focus()


class WifiAccessPointSlot(Box):
    """WiFi access point list item with detailed info and inline password entry"""

    def __init__(self, ap_data: dict, network_service: NetworkClient, wifi_service, **kwargs):
        super().__init__(orientation="v", spacing=8, name="wifi-ap-slot", **kwargs)
        self.ap_data = ap_data
        self.network_service = network_service
        self.wifi_service = wifi_service

        ssid = ap_data.get("ssid", "Unknown SSID")
        icon_name = ap_data.get("icon-name", "network-wireless-signal-none-symbolic")
        strength = ap_data.get("strength", 0)
        frequency = ap_data.get("frequency", 0)
        security = ap_data.get("security", "Unknown")
        self.requires_password = ap_data.get("requires_password", False)
        self.ssid = ssid

        # Truncate very long SSIDs for better display
        display_ssid = ssid if len(ssid) <= 25 else ssid[:22] + "..."

        # Check if this is the active AP
        self.is_active = False
        active_ap_details = ap_data.get("active-ap")
        if active_ap_details and hasattr(active_ap_details, 'get_bssid') and active_ap_details.get_bssid() == ap_data.get("bssid"):
            self.is_active = True

        # Icon
        self.ap_icon = Image(icon_name=icon_name, pixel_size=24)

        # Security icon
        if security != "Open":
            security_icon = "󰌾"
        else:
            security_icon = "󰿆"

        # Frequency band
        freq_band = "5GHz" if frequency > 5000 else "2.4GHz"

        # SSID label with detailed info
        info_text = f"{display_ssid}\n<small>{strength}% • {freq_band} • {security}</small>"
        self.ap_label = Label(
            markup=info_text,
            h_expand=True,
            h_align="start",
            use_markup=True,
            ellipsize="end",  # Ellipsize at end if still too long
            max_width_chars=30
        )

        # Connect button
        self.connect_button = Button(
            name="wifi-connect-button",
            label="Connected" if self.is_active else "Connect",
            sensitive=not self.is_active,
            on_clicked=self._on_connect_clicked,
        )

        if self.is_active:
            self.connect_button.add_style_class("connected")

        # Top row with icon, label, and connect button
        info_box = Box(
            spacing=12,
            h_expand=True,
            h_align="fill",
            children=[
                self.ap_icon,
                self.ap_label,
            ]
        )

        top_row = CenterBox(
            name="wifi-ap-top-row",
            start_children=[info_box],
            end_children=[self.connect_button]
        )

        self.add(top_row)

        # Password entry row (hidden by default)
        self.password_entry_row = None
        self.password_entry_visible = False

    def _on_connect_clicked(self, _):
        if not self.is_active:
            if self.requires_password:
                # Show inline password entry
                self._show_password_entry()
            else:
                # Open network, connect directly
                self._connect_with_password(None)

    def _show_password_entry(self):
        if not self.password_entry_visible:
            self.password_entry_row = PasswordEntryRow(
                self.ssid,
                self._connect_with_password,
                self._hide_password_entry
            )
            self.add(self.password_entry_row)
            self.password_entry_row.show_all()
            self.password_entry_row.grab_entry_focus()
            self.password_entry_visible = True

    def _hide_password_entry(self):
        if self.password_entry_visible and self.password_entry_row:
            self.remove(self.password_entry_row)
            self.password_entry_row.destroy()
            self.password_entry_row = None
            self.password_entry_visible = False

    def _connect_with_password(self, password):
        bssid = self.ap_data.get("bssid")
        if bssid:
            self.connect_button.set_label("Connecting...")
            self.connect_button.set_sensitive(False)
            self._hide_password_entry()
            self.network_service.connect_wifi_bssid(bssid, password)


class NetworkWidget(BasePopup):
    """Network management popup with WiFi and Ethernet info"""

    def __init__(self, **kwargs):
        self.network_client = NetworkClient()
        self.status_label = None
        self.wifi_toggle_button = None
        self.wifi_toggle_icon = None
        self.refresh_button = None
        self.ap_list_box = None
        self.ethernet_info_box = None
        self.current_connection_box = None

        super().__init__(
            name="network-widget",
            anchor="top right",
            margin="8px 20px 0px 0px",
            width=550,
            **kwargs
        )

    def build_content(self):
        """Build the network widget content"""
        # Current connection info
        self.current_connection_box = Box(
            orientation="v",
            spacing=4,
            name="current-connection-box"
        )

        # Status label (shown during scanning)
        self.status_label = Label(
            label="Initializing network...",
            h_expand=True,
            h_align="center",
            name="network-status"
        )

        # WiFi toggle button
        self.wifi_toggle_icon = Label(markup="󰤨", name="wifi-toggle-icon")
        self.wifi_toggle_button = Button(
            name="wifi-toggle-button",
            child=self.wifi_toggle_icon,
            tooltip_text="Toggle Wi-Fi",
            on_clicked=self._toggle_wifi,
            sensitive=False
        )

        # Refresh button
        refresh_icon = Label(markup="󰑓", name="network-refresh-icon")
        self.refresh_button = Button(
            name="network-refresh",
            child=refresh_icon,
            tooltip_text="Scan for Wi-Fi networks",
            on_clicked=self._refresh_access_points,
            sensitive=False
        )

        # Header
        header_box = CenterBox(
            name="network-header",
            start_children=[
                Label(
                    label="󰀂 Network",
                    name="network-title",
                    style="font-size: 16px; font-weight: bold;"
                )
            ],
            end_children=[
                Box(
                    orientation="h",
                    spacing=8,
                    children=[self.refresh_button, self.wifi_toggle_button]
                )
            ]
        )

        # Ethernet section
        self.ethernet_info_box = Box(
            orientation="v",
            spacing=8,
            name="ethernet-section"
        )

        # Access points list
        self.ap_list_box = Box(
            orientation="v",
            spacing=4,
            name="ap-list-box"
        )

        # WiFi section with scrollable list
        wifi_label = Label(
            label="Available Networks",
            name="section-title",
            h_align="start",
            style="font-size: 14px; font-weight: bold; margin-top: 8px;"
        )

        scrolled_window = ScrolledWindow(
            name="network-ap-scrolled-window",
            child=self.ap_list_box,
            h_expand=True,
            v_expand=True,
            min_content_size=(530, 100),
            max_content_size=(530, 400),
        )

        # Main content
        content = Box(
            orientation="v",
            spacing=12,
            name="network-content",
            children=[
                header_box,
                self.current_connection_box,
                self.ethernet_info_box,
                wifi_label,
                self.status_label,
                scrolled_window,
            ]
        )

        # Set up network client callbacks
        self.network_client.connect("device-ready", self._on_device_ready)

        return content

    def _on_device_ready(self, _client):
        """Called when network device is ready"""
        # Set up WiFi
        if self.network_client.wifi_device:
            self.network_client.wifi_device.connect("changed", self._on_wifi_changed)
            self.network_client.wifi_device.connect("notify::enabled", self._update_wifi_status_ui)
            self._update_wifi_status_ui()

            if self.network_client.wifi_device.enabled:
                self._load_access_points()
        else:
            self.wifi_toggle_button.set_sensitive(False)
            self.refresh_button.set_sensitive(False)

        # Set up Ethernet
        if self.network_client.ethernet_device:
            self.network_client.ethernet_device.connect("changed", self._update_ethernet_info)
            self._update_ethernet_info()

        self._update_current_connection()

    def _update_current_connection(self):
        """Update current connection information"""
        for child in self.current_connection_box.get_children():
            child.destroy()

        if self.network_client.wifi_device and self.network_client.wifi_device.internet == "activated":
            ssid = self.network_client.wifi_device.ssid
            strength = self.network_client.wifi_device.strength
            frequency = self.network_client.wifi_device.frequency
            bandwidth = self.network_client.wifi_device.bandwidth
            freq_band = "5GHz" if frequency > 5000 else "2.4GHz"

            info_label = Label(
                markup=f"<b>󰤨 Connected to:</b> {ssid}\n<small>Signal: {strength}% • {freq_band} ({frequency} MHz) • {bandwidth}</small>",
                name="current-connection-info",
                h_align="start",
                use_markup=True
            )
            self.current_connection_box.add(info_label)
            self.current_connection_box.show_all()

            # Set up bandwidth update only once
            if not hasattr(self, '_bandwidth_update_id'):
                self._bandwidth_update_id = GLib.timeout_add(1000, self._update_current_connection_bandwidth)

            return False  # Don't continue if called from timeout
        else:
            self.current_connection_box.hide()
            # Stop bandwidth updates if disconnected
            if hasattr(self, '_bandwidth_update_id'):
                GLib.source_remove(self._bandwidth_update_id)
                delattr(self, '_bandwidth_update_id')
            return False

    def _update_current_connection_bandwidth(self):
        """Update only the bandwidth information without recreating widgets"""
        if self.network_client.wifi_device and self.network_client.wifi_device.internet == "activated":
            # Just update the existing label
            for child in self.current_connection_box.get_children():
                if isinstance(child, Label):
                    ssid = self.network_client.wifi_device.ssid
                    strength = self.network_client.wifi_device.strength
                    frequency = self.network_client.wifi_device.frequency
                    bandwidth = self.network_client.wifi_device.bandwidth
                    freq_band = "5GHz" if frequency > 5000 else "2.4GHz"

                    child.set_markup(f"<b>󰤨 Connected to:</b> {ssid}\n<small>Signal: {strength}% • {freq_band} ({frequency} MHz) • {bandwidth}</small>")
            return True  # Continue timeout
        else:
            # Disconnected, stop updates
            if hasattr(self, '_bandwidth_update_id'):
                delattr(self, '_bandwidth_update_id')
            return False

    def _update_ethernet_info(self, *args):
        """Update Ethernet connection information"""
        for child in self.ethernet_info_box.get_children():
            child.destroy()

        if self.network_client.ethernet_device:
            state = self.network_client.ethernet_device.state
            speed = self.network_client.ethernet_device.speed
            bandwidth = self.network_client.ethernet_device.bandwidth

            if state == "activated":
                icon = "󰈁"
                status_text = f"<b>{icon} Ethernet:</b> Connected"
                if speed > 0:
                    status_text += f"\n<small>Link: {speed} Mb/s • {bandwidth}</small>"

                eth_label = Label(
                    markup=status_text,
                    name="ethernet-info",
                    h_align="start",
                    use_markup=True
                )
                self.ethernet_info_box.add(eth_label)
                self.ethernet_info_box.show_all()

                # Set up bandwidth update for Ethernet only once
                if not hasattr(self, '_eth_bandwidth_update_id'):
                    self._eth_bandwidth_update_id = GLib.timeout_add(1000, self._update_ethernet_bandwidth)

                return False  # Don't continue if called from timeout
            else:
                self.ethernet_info_box.hide()
                # Stop bandwidth updates if disconnected
                if hasattr(self, '_eth_bandwidth_update_id'):
                    GLib.source_remove(self._eth_bandwidth_update_id)
                    delattr(self, '_eth_bandwidth_update_id')
                return False
        else:
            self.ethernet_info_box.hide()
            return False

    def _update_ethernet_bandwidth(self):
        """Update only Ethernet bandwidth without recreating widgets"""
        if self.network_client.ethernet_device and self.network_client.ethernet_device.state == "activated":
            # Just update the existing label
            for child in self.ethernet_info_box.get_children():
                if isinstance(child, Label):
                    speed = self.network_client.ethernet_device.speed
                    bandwidth = self.network_client.ethernet_device.bandwidth
                    icon = "󰈁"
                    status_text = f"<b>{icon} Ethernet:</b> Connected"
                    if speed > 0:
                        status_text += f"\n<small>Link: {speed} Mb/s • {bandwidth}</small>"

                    child.set_markup(status_text)
            return True  # Continue timeout
        else:
            # Disconnected, stop updates
            if hasattr(self, '_eth_bandwidth_update_id'):
                delattr(self, '_eth_bandwidth_update_id')
            return False

    def _on_wifi_changed(self, *args):
        """Handle WiFi changes"""
        self._load_access_points()
        self._update_current_connection()

    def _update_wifi_status_ui(self, *args):
        """Update UI based on WiFi status"""
        if self.network_client.wifi_device:
            enabled = self.network_client.wifi_device.enabled
            self.wifi_toggle_button.set_sensitive(True)
            self.refresh_button.set_sensitive(enabled)

            if enabled:
                self.wifi_toggle_icon.set_markup("󰤨")
            else:
                self.wifi_toggle_icon.set_markup("󰤭")
                self.status_label.set_label("Wi-Fi disabled.")
                self.status_label.set_visible(True)
                self._clear_ap_list()

            if enabled and not self.ap_list_box.get_children():
                GLib.idle_add(self._refresh_access_points)
        else:
            self.wifi_toggle_button.set_sensitive(False)
            self.refresh_button.set_sensitive(False)

    def _toggle_wifi(self, _):
        """Toggle WiFi on/off"""
        if self.network_client.wifi_device:
            self.network_client.wifi_device.toggle_wifi()

    def _refresh_access_points(self, _=None):
        """Scan for WiFi networks"""
        if self.network_client.wifi_device and self.network_client.wifi_device.enabled:
            self.status_label.set_label("Scanning for Wi-Fi networks...")
            self.status_label.set_visible(True)
            self._clear_ap_list()
            self.network_client.wifi_device.scan()
        return False

    def _clear_ap_list(self):
        """Clear access points list"""
        for child in self.ap_list_box.get_children():
            child.destroy()

    def _load_access_points(self, *args):
        """Load and display access points"""
        if not self.network_client.wifi_device or not self.network_client.wifi_device.enabled:
            self._clear_ap_list()
            self.status_label.set_label("Wi-Fi disabled.")
            self.status_label.set_visible(True)
            return

        self._clear_ap_list()

        access_points = self.network_client.wifi_device.access_points

        if not access_points:
            self.status_label.set_label("No Wi-Fi networks found.")
            self.status_label.set_visible(True)
        else:
            self.status_label.set_visible(False)
            # Sort by signal strength
            sorted_aps = sorted(access_points, key=lambda x: x.get("strength", 0), reverse=True)

            # Remove duplicates (same SSID, keep strongest)
            seen_ssids = set()
            unique_aps = []
            for ap in sorted_aps:
                ssid = ap.get("ssid", "")
                if ssid and ssid not in seen_ssids:
                    seen_ssids.add(ssid)
                    unique_aps.append(ap)

            # Add access points
            for ap_data in unique_aps:
                slot = WifiAccessPointSlot(
                    ap_data,
                    self.network_client,
                    self.network_client.wifi_device
                )
                self.ap_list_box.add(slot)

        self.ap_list_box.show_all()

    def on_open(self):
        """Called when widget opens"""
        if self.network_client.wifi_device and self.network_client.wifi_device.enabled:
            self._refresh_access_points()
        self._update_current_connection()
        self._update_ethernet_info()

    def on_close(self):
        """Called before close animation"""
        pass


# Singleton instance
network_widget = None


def get_network_widget():
    """Get or create the network widget singleton"""
    global network_widget
    if network_widget is None:
        network_widget = NetworkWidget()
    return network_widget
