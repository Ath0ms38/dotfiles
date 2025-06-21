// AGS v2 Network Widget

import Network from "gi://AstalNetwork"
import Bluetooth from "gi://AstalBluetooth"
import Gtk from "gi://Gtk?version=3.0"
import { bind, Variable } from "astal"
import { execAsync } from "astal/process"

export default function NetworkWidget({ fullView = false }: { fullView?: boolean }) {
    const network = Network.get_default()
    const bluetooth = Bluetooth.get_default()
    const showWifiList = Variable(false)

    if (fullView) {
        return <box className="network-widget-full" vertical spacing={12}>
            <label className="widget-title" label="📶 Network & Connectivity" />
            
            {/* WiFi section */}
            <box className="wifi-section" vertical spacing={8}>
                <box className="wifi-header" spacing={12}>
                    <label className="section-label" label="WiFi" />
                    <box hexpand />
                    <switch active={bind(network.wifi, "enabled")}
                        onActivate={({ active }) => network.wifi && (network.wifi.enabled = active)} />
                </box>
                
                {bind(network.wifi, "enabled").as(enabled => enabled && (
                    <box vertical spacing={6}>
                        <box className="current-network" spacing={8}>
                            <icon icon={bind(network.wifi, "iconName")} />
                            <label label={bind(network.wifi, "ssid").as(ssid => ssid || "Not connected")} />
                            <label className="signal-strength" 
                                label={bind(network.wifi, "strength").as(s => `${s}%`)} />
                        </box>
                        
                        <button className="scan-button" 
                            onClicked={() => {
                                network.wifi?.scan()
                                showWifiList.set(!showWifiList.get())
                            }}>
                            {bind(showWifiList).as(show => show ? "Hide Networks" : "Show Networks")}
                        </button>
                        
                        <revealer revealChild={bind(showWifiList)} transitionType={Gtk.RevealerTransitionType.SLIDE_DOWN}>
                            <scrollable heightRequest={150}>
                                <box className="wifi-list" vertical spacing={4}>
                                    {bind(network.wifi, "accessPoints").as(aps => 
                                        aps.map(ap => (
                                            <button key={ap.bssid} className="wifi-item"
                                                onClicked={() => execAsync(["nmcli", "device", "wifi", "connect", ap.ssid])}>
                                                <box spacing={8}>
                                                    <icon icon={ap.iconName} />
                                                    <label label={ap.ssid} hexpand />
                                                    <label label={`${ap.strength}%`} />
                                                    {ap.secure && <icon icon="network-wireless-encrypted-symbolic" />}
                                                </box>
                                            </button>
                                        ))
                                    )}
                                </box>
                            </scrollable>
                        </revealer>
                    </box>
                ))}
            </box>

            {/* Bluetooth section */}
            <box className="bluetooth-section" vertical spacing={8}>
                <box className="bluetooth-header" spacing={12}>
                    <label className="section-label" label="Bluetooth" />
                    <box hexpand />
                    <switch active={bind(bluetooth, "isPowered")}
                        onActivate={({ active }) => bluetooth.adapter?.setPowered(active)} />
                </box>
                
                {bind(bluetooth, "isPowered").as(powered => powered && (
                    <box vertical spacing={6}>
                        <box className="connected-devices" vertical spacing={4}>
                            {bind(bluetooth, "devices").as(devices => 
                                devices.filter(d => d.connected).map(device => (
                                    <box key={device.address} className="bluetooth-device" spacing={8}>
                                        <icon icon={device.icon} />
                                        <label label={device.name} hexpand />
                                        <button className="disconnect-button"
                                            onClicked={() => device.disconnect()}>
                                            Disconnect
                                        </button>
                                    </box>
                                ))
                            )}
                        </box>
                        
                        <button className="scan-button"
                            onClicked={() => bluetooth.adapter?.startDiscovery()}>
                            Scan for Devices
                        </button>
                    </box>
                ))}
            </box>

            {/* Quick actions */}
            <box className="network-actions" spacing={6}>
                <button className="action-button" onClicked={() => execAsync(["kitty", "-e", "nmtui"])}>
                    Network Settings
                </button>
                <button className="action-button" onClicked={() => execAsync(["blueman-manager"])}>
                    Bluetooth Manager
                </button>
            </box>
        </box>
    }

    return <box className="network-widget-compact">
        <icon icon="network-wireless-symbolic" />
    </box>
}