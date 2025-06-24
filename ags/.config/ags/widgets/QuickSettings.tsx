// ags/.config/ags/widgets/QuickSettings.tsx

import { Variable, bind } from "astal"
import Network from "gi://AstalNetwork"
import Bluetooth from "gi://AstalBluetooth"
import { execAsync } from "astal/process"
import { Widget } from "astal/gtk3"

const dndEnabled = Variable(false)
const nightLightEnabled = Variable(false)
const airplaneModeEnabled = Variable(false)

export default function QuickSettingsWidget({ fullView = false }: { fullView?: boolean }) {
    const network = Network.get_default()
    const bluetooth = Bluetooth.get_default()

    if (fullView) {
        return new Widget.Box({
            className: "quick-settings-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "⚡ Quick Settings"
                }),
                
                // Toggle grid
                new Widget.Box({
                    className: "toggle-grid",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Box({
                            spacing: 8,
                            children: [
                                new Widget.Button({
                                    className: bind(network.wifi, "enabled").as(e => `toggle-button ${e ? "active" : ""}`),
                                    onClicked: () => network.wifi && (network.wifi.enabled = !network.wifi.enabled),
                                    child: new Widget.Box({
                                        vertical: true,
                                        spacing: 4,
                                        children: [
                                            new Widget.Icon({ icon: "network-wireless-symbolic", iconSize: 24 }),
                                            new Widget.Label({ label: "WiFi" })
                                        ]
                                    })
                                }),
                                
                                new Widget.Button({
                                    className: bind(bluetooth, "isPowered").as(p => `toggle-button ${p ? "active" : ""}`),
                                    onClicked: () => bluetooth.adapter?.setPowered(!bluetooth.isPowered),
                                    child: new Widget.Box({
                                        vertical: true,
                                        spacing: 4,
                                        children: [
                                            new Widget.Icon({ icon: "bluetooth-symbolic", iconSize: 24 }),
                                            new Widget.Label({ label: "Bluetooth" })
                                        ]
                                    })
                                }),
                                
                                new Widget.Button({
                                    className: bind(dndEnabled).as(e => `toggle-button ${e ? "active" : ""}`),
                                    onClicked: () => {
                                        dndEnabled.set(!dndEnabled.get())
                                        execAsync(["swaync-client", "-d"])
                                    },
                                    child: new Widget.Box({
                                        vertical: true,
                                        spacing: 4,
                                        children: [
                                            new Widget.Icon({ icon: "dialog-information-symbolic", iconSize: 24 }),
                                            new Widget.Label({ label: "Do Not Disturb" })
                                        ]
                                    })
                                })
                            ]
                        }),
                        
                        new Widget.Box({
                            spacing: 8,
                            children: [
                                new Widget.Button({
                                    className: bind(nightLightEnabled).as(e => `toggle-button ${e ? "active" : ""}`),
                                    onClicked: () => {
                                        nightLightEnabled.set(!nightLightEnabled.get())
                                        execAsync(["hyprshade", "toggle"])
                                    },
                                    child: new Widget.Box({
                                        vertical: true,
                                        spacing: 4,
                                        children: [
                                            new Widget.Icon({ icon: "night-light-symbolic", iconSize: 24 }),
                                            new Widget.Label({ label: "Night Light" })
                                        ]
                                    })
                                }),
                                
                                new Widget.Button({
                                    className: bind(airplaneModeEnabled).as(e => `toggle-button ${e ? "active" : ""}`),
                                    onClicked: () => {
                                        airplaneModeEnabled.set(!airplaneModeEnabled.get())
                                        if (airplaneModeEnabled.get()) {
                                            network.wifi && (network.wifi.enabled = false)
                                            bluetooth.adapter?.setPowered(false)
                                        } else {
                                            network.wifi && (network.wifi.enabled = true)
                                            bluetooth.adapter?.setPowered(true)
                                        }
                                    },
                                    child: new Widget.Box({
                                        vertical: true,
                                        spacing: 4,
                                        children: [
                                            new Widget.Icon({ icon: "airplane-mode-symbolic", iconSize: 24 }),
                                            new Widget.Label({ label: "Airplane Mode" })
                                        ]
                                    })
                                }),
                                
                                new Widget.Button({
                                    className: "toggle-button",
                                    onClicked: () => execAsync(["hyprpicker", "-a"]),
                                    child: new Widget.Box({
                                        vertical: true,
                                        spacing: 4,
                                        children: [
                                            new Widget.Icon({ icon: "applications-graphics-symbolic", iconSize: 24 }),
                                            new Widget.Label({ label: "Color Picker" })
                                        ]
                                    })
                                })
                            ]
                        })
                    ]
                }),

                // Screenshot tools
                new Widget.Box({
                    className: "screenshot-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Screenshot"
                        }),
                        new Widget.Box({
                            spacing: 6,
                            children: [
                                new Widget.Button({
                                    className: "action-button",
                                    label: "Area",
                                    onClicked: () => execAsync(["grimblast", "copy", "area"])
                                }),
                                new Widget.Button({
                                    className: "action-button",
                                    label: "Window",
                                    onClicked: () => execAsync(["grimblast", "copy", "active"])
                                }),
                                new Widget.Button({
                                    className: "action-button",
                                    label: "Full Screen",
                                    onClicked: () => execAsync(["grimblast", "copy", "screen"])
                                })
                            ]
                        })
                    ]
                }),

                // Screen recording
                new Widget.Box({
                    className: "recording-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Screen Recording"
                        }),
                        new Widget.Button({
                            className: "record-button",
                            label: "Start Recording",
                            onClicked: () => execAsync(["wf-recorder", "-g", "$(slurp)"])
                        })
                    ]
                }),

                // System services
                new Widget.Box({
                    className: "services-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "System Services"
                        }),
                        new Widget.Box({
                            spacing: 6,
                            children: [
                                new Widget.Button({
                                    className: "action-button",
                                    label: "Restart Waybar",
                                    onClicked: () => execAsync(["systemctl", "--user", "restart", "waybar"])
                                }),
                                new Widget.Button({
                                    className: "action-button",
                                    label: "Reload Hyprland",
                                    onClicked: () => execAsync(["hyprctl", "reload"])
                                })
                            ]
                        })
                    ]
                })
            ]
        })
    }

    return new Widget.Box({
        className: "quick-settings-compact",
        children: [new Widget.Icon({ icon: "emblem-system-symbolic" })]
    })
}
