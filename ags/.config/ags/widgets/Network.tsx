// ags/.config/ags/widgets/Network.tsx

import Network from "gi://AstalNetwork"
import Bluetooth from "gi://AstalBluetooth"
import Gtk from "gi://Gtk?version=3.0"
import { bind, Variable } from "astal"
import { execAsync } from "astal/process"
import { Widget } from "astal/gtk3"

export default function NetworkWidget({ fullView = false }: { fullView?: boolean }) {
    const network = Network.get_default()
    const bluetooth = Bluetooth.get_default()
    const showWifiList = Variable(false)

    if (fullView) {
        return new Widget.Box({
            className: "network-widget-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "📶 Network & Connectivity"
                }),
                
                // WiFi section
                new Widget.Box({
                    className: "wifi-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Box({
                            className: "wifi-header",
                            spacing: 12,
                            children: [
                                new Widget.Label({
                                    className: "section-label",
                                    label: "WiFi"
                                }),
                                new Widget.Box({ hexpand: true }),
                                // @ts-ignore - switch widget
                                new Widget.Switch({
                                    active: bind(network.wifi, "enabled"),
                                    onActivate: ({ active }: any) => network.wifi && (network.wifi.enabled = active)
                                })
                            ]
                        }),
                        
                        bind(network.wifi, "enabled").as(enabled => enabled ? new Widget.Box({
                            vertical: true,
                            spacing: 6,
                            children: [
                                new Widget.Box({
                                    className: "current-network",
                                    spacing: 8,
                                    children: [
                                        new Widget.Icon({
                                            icon: bind(network.wifi, "iconName")
                                        }),
                                        new Widget.Label({
                                            label: bind(network.wifi, "ssid").as(ssid => ssid || "Not connected")
                                        }),
                                        new Widget.Label({
                                            className: "signal-strength",
                                            label: bind(network.wifi, "strength").as(s => `${s}%`)
                                        })
                                    ]
                                }),
                                
                                new Widget.Button({
                                    className: "scan-button",
                                    label: bind(showWifiList).as(show => show ? "Hide Networks" : "Show Networks"),
                                    onClicked: () => {
                                        network.wifi?.scan()
                                        showWifiList.set(!showWifiList.get())
                                    }
                                }),
                                
                                // @ts-ignore - revealer widget
                                new Widget.Revealer({
                                    revealChild: bind(showWifiList),
                                    transitionType: Gtk.RevealerTransitionType.SLIDE_DOWN,
                                    // @ts-ignore - scrollable widget
                                    child: new Widget.Scrollable({
                                        heightRequest: 150,
                                        child: new Widget.Box({
                                            className: "wifi-list",
                                            vertical: true,
                                            spacing: 4,
                                            children: bind(network.wifi, "accessPoints").as(aps => 
                                                aps.map(ap => new Widget.Button({
                                                    className: "wifi-item",
                                                    onClicked: () => execAsync(["nmcli", "device", "wifi", "connect", ap.ssid]),
                                                    child: new Widget.Box({
                                                        spacing: 8,
                                                        children: [
                                                            new Widget.Icon({ icon: ap.iconName }),
                                                            new Widget.Label({ label: ap.ssid, hexpand: true }),
                                                            new Widget.Label({ label: `${ap.strength}%` }),
                                                            ap.secure ? new Widget.Icon({ icon: "network-wireless-encrypted-symbolic" }) : new Widget.Box({})
                                                        ]
                                                    })
                                                }))
                                            )
                                        })
                                    })
                                })
                            ]
                        }) : new Widget.Box({}))
                    ]
                }),

                // Bluetooth section
                new Widget.Box({
                    className: "bluetooth-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Box({
                            className: "bluetooth-header",
                            spacing: 12,
                            children: [
                                new Widget.Label({
                                    className: "section-label",
                                    label: "Bluetooth"
                                }),
                                new Widget.Box({ hexpand: true }),
                                // @ts-ignore - switch widget
                                new Widget.Switch({
                                    active: bind(bluetooth, "isPowered"),
                                    onActivate: ({ active }: any) => bluetooth.adapter?.setPowered(active)
                                })
                            ]
                        }),
                        
                        bind(bluetooth, "isPowered").as(powered => powered ? new Widget.Box({
                            vertical: true,
                            spacing: 6,
                            children: [
                                new Widget.Box({
                                    className: "connected-devices",
                                    vertical: true,
                                    spacing: 4,
                                    children: bind(bluetooth, "devices").as(devices => 
                                        devices.filter(d => d.connected).map(device => new Widget.Box({
                                            className: "bluetooth-device",
                                            spacing: 8,
                                            children: [
                                                new Widget.Icon({ icon: device.icon }),
                                                new Widget.Label({ label: device.name, hexpand: true }),
                                                new Widget.Button({
                                                    className: "disconnect-button",
                                                    label: "Disconnect",
                                                    onClicked: () => device.disconnect()
                                                })
                                            ]
                                        }))
                                    )
                                }),
                                
                                new Widget.Button({
                                    className: "scan-button",
                                    label: "Scan for Devices",
                                    onClicked: () => bluetooth.adapter?.startDiscovery()
                                })
                            ]
                        }) : new Widget.Box({}))
                    ]
                }),

                // Quick actions
                new Widget.Box({
                    className: "network-actions",
                    spacing: 6,
                    children: [
                        new Widget.Button({
                            className: "action-button",
                            label: "Network Settings",
                            onClicked: () => execAsync(["kitty", "-e", "nmtui"])
                        }),
                        new Widget.Button({
                            className: "action-button",
                            label: "Bluetooth Manager",
                            onClicked: () => execAsync(["blueman-manager"])
                        })
                    ]
                })
            ]
        })
    }

    return new Widget.Box({
        className: "network-widget-compact",
        children: [new Widget.Icon({ icon: "network-wireless-symbolic" })]
    })
}
