// ags/.config/ags/widgets/PowerDisplay.tsx

import { bind, Variable } from "astal"
import { execAsync } from "astal/process"
import Battery from "gi://AstalBattery"
import { Widget } from "astal/gtk3"

const brightness = Variable(50).poll(5000, async () => {
    const max = await execAsync(["brightnessctl", "max"]).then(out => parseInt(out)).catch(() => 255)
    const current = await execAsync(["brightnessctl", "get"]).then(out => parseInt(out)).catch(() => 128)
    return Math.round((current / max) * 100)
})

const powerProfile = Variable("balanced").poll(10000, () =>
    execAsync(["powerprofilesctl", "get"]).then(out => out.trim()).catch(() => "balanced")
)

const presetLevels = [25, 50, 75, 100]

export default function PowerDisplayWidget({ fullView = false }: { fullView?: boolean }) {
    const battery = Battery.get_default()

    if (fullView) {
        return new Widget.Box({
            className: "power-display-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "🔋 Power & Display"
                }),
                
                // Battery Section
                battery ? new Widget.Box({
                    className: "battery-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Battery"
                        }),
                        new Widget.Box({
                            spacing: 12,
                            children: [
                                new Widget.Icon({
                                    icon: bind(battery, "batteryIconName"),
                                    iconSize: 32
                                }),
                                new Widget.Box({
                                    vertical: true,
                                    children: [
                                        new Widget.Label({
                                            label: bind(battery, "percentage").as(p => `${p}%`)
                                        }),
                                        new Widget.Label({
                                            className: "battery-status",
                                            label: bind(battery, "charging").as(c => c ? "Charging" : "Discharging")
                                        }),
                                        new Widget.Label({
                                            className: "battery-time",
                                            label: bind(battery, "timeToEmpty").as(t => {
                                                if (t === 0) return ""
                                                const hours = Math.floor(t / 3600)
                                                const minutes = Math.floor((t % 3600) / 60)
                                                return `${hours}h ${minutes}m remaining`
                                            })
                                        })
                                    ]
                                })
                            ]
                        })
                    ]
                }) : new Widget.Box({}),

                // Brightness Section
                new Widget.Box({
                    className: "brightness-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Brightness"
                        }),
                        new Widget.Box({
                            spacing: 12,
                            children: [
                                new Widget.Icon({ icon: "display-brightness-symbolic" }),
                                new Widget.Slider({
                                    className: "brightness-slider",
                                    min: 5,
                                    max: 100,
                                    value: bind(brightness),
                                    onDragged: ({ value }: any) => {
                                        const val = Math.round(value)
                                        execAsync(["brightnessctl", "set", `${val}%`])
                                        brightness.set(val)
                                    },
                                    drawValue: false,
                                    hexpand: true,
                                }),
                                new Widget.Label({
                                    label: bind(brightness).as(b => `${b}%`)
                                })
                            ]
                        }),
                        new Widget.Box({
                            className: "brightness-presets",
                            spacing: 6,
                            children: presetLevels.map(level => new Widget.Button({
                                className: "preset-button",
                                label: `${level}%`,
                                onClicked: () => {
                                    execAsync(["brightnessctl", "set", `${level}%`])
                                    brightness.set(level)
                                }
                            }))
                        })
                    ]
                }),

                // Power Profile Section
                new Widget.Box({
                    className: "power-profile-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Power Profile"
                        }),
                        new Widget.Box({
                            className: "profile-buttons",
                            spacing: 6,
                            children: [
                                new Widget.Button({
                                    className: bind(powerProfile).as(p => `profile-button ${p === "power-saver" ? "active" : ""}`),
                                    label: "Power Saver",
                                    onClicked: () => {
                                        execAsync(["powerprofilesctl", "set", "power-saver"])
                                        powerProfile.set("power-saver")
                                    }
                                }),
                                new Widget.Button({
                                    className: bind(powerProfile).as(p => `profile-button ${p === "balanced" ? "active" : ""}`),
                                    label: "Balanced",
                                    onClicked: () => {
                                        execAsync(["powerprofilesctl", "set", "balanced"])
                                        powerProfile.set("balanced")
                                    }
                                }),
                                new Widget.Button({
                                    className: bind(powerProfile).as(p => `profile-button ${p === "performance" ? "active" : ""}`),
                                    label: "Performance",
                                    onClicked: () => {
                                        execAsync(["powerprofilesctl", "set", "performance"])
                                        powerProfile.set("performance")
                                    }
                                })
                            ]
                        })
                    ]
                }),

                // Display Settings
                new Widget.Box({
                    className: "display-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Display Settings"
                        }),
                        new Widget.Box({
                            className: "display-actions",
                            spacing: 6,
                            children: [
                                new Widget.Button({
                                    className: "action-button",
                                    label: "Display Configuration",
                                    onClicked: () => execAsync(["wdisplays"])
                                }),
                                new Widget.Button({
                                    className: "action-button",
                                    label: "Night Light",
                                    onClicked: () => execAsync(["hyprctl", "dispatch", "exec", "hyprshade toggle"])
                                })
                            ]
                        })
                    ]
                })
            ]
        })
    }

    return new Widget.Box({
        className: "power-display-compact",
        children: [new Widget.Icon({ icon: "battery-symbolic" })]
    })
}
