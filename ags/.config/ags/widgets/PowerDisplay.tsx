// AGS v2 Power/Display Widget

import { bind, Variable } from "astal"
import { execAsync } from "astal/process"
import Battery from "gi://AstalBattery"
import { Widget } from "astal/gtk3"
import Gtk from "gi://Gtk?version=3.0"

const brightness = Variable(50).poll(5000, async () => {
    const max = await execAsync(["brightnessctl", "max"]).then(out => parseInt(out)).catch(() => 255)
    const current = await execAsync(["brightnessctl", "get"]).then(out => parseInt(out)).catch(() => 128)
    return Math.round((current / max) * 100)
})

const powerProfile = Variable("balanced").poll(10000, () =>
    execAsync(["powerprofilesctl", "get"]).then(out => out.trim()).catch(() => "balanced")
)

export default function PowerDisplayWidget({ fullView = false }: { fullView?: boolean }) {
    const battery = Battery.get_default()

    if (fullView) {
        return <box className="power-display-full" vertical spacing={12}>
            <label className="widget-title" label="🔋 Power & Display" />
            
            {/* Battery Section */}
            {battery && (
                <box className="battery-section" vertical spacing={8}>
                    <label className="section-label" label="Battery" />
                    <box spacing={12}>
                        <icon icon={bind(battery, "batteryIconName")} iconSize={32} />
                        <box vertical>
                            <label label={bind(battery, "percentage").as(p => `${p}%`)} />
                            <label className="battery-status" 
                                label={bind(battery, "charging").as(c => c ? "Charging" : "Discharging")} />
                            <label className="battery-time" 
                                label={bind(battery, "timeToEmpty").as(t => {
                                    if (t === 0) return ""
                                    const hours = Math.floor(t / 3600)
                                    const minutes = Math.floor((t % 3600) / 60)
                                    return `${hours}h ${minutes}m remaining`
                                })} />
                        </box>
                    </box>
                </box>
            )}

            {/* Brightness Section */}
            <box className="brightness-section" vertical spacing={8}>
                <label className="section-label" label="Brightness" />
                <box spacing={12}>
                    <icon icon="display-brightness-symbolic" />
                    {new Widget.Slider({
                        className: "brightness-slider",
                        min: 5,
                        max: 100,
                        value: bind(brightness),
                        onDragged: ({ value }) => {
                            const val = Math.round(value)
                            execAsync(["brightnessctl", "set", `${val}%`])
                            brightness.set(val)
                        },
                        drawValue: false,
                        hexpand: true,
                    })}
                    <label label={bind(brightness).as(b => `${b}%`)} />
                </box>
                <box className="brightness-presets" spacing={6}>
                    {[25, 50, 75, 100].map(level => (
                        <button key={level} className="preset-button"
                            onClicked={() => {
                                execAsync(["brightnessctl", "set", `${level}%`])
                                brightness.set(level)
                            }}>
                            {level}%
                        </button>
                    ))}
                </box>
            </box>

            {/* Power Profile Section */}
            <box className="power-profile-section" vertical spacing={8}>
                <label className="section-label" label="Power Profile" />
                <box className="profile-buttons" spacing={6}>
                    <button className={bind(powerProfile).as(p => `profile-button ${p === "power-saver" ? "active" : ""}`)}
                        onClicked={() => {
                            execAsync(["powerprofilesctl", "set", "power-saver"])
                            powerProfile.set("power-saver")
                        }}>
                        Power Saver
                    </button>
                    <button className={bind(powerProfile).as(p => `profile-button ${p === "balanced" ? "active" : ""}`)}
                        onClicked={() => {
                            execAsync(["powerprofilesctl", "set", "balanced"])
                            powerProfile.set("balanced")
                        }}>
                        Balanced
                    </button>
                    <button className={bind(powerProfile).as(p => `profile-button ${p === "performance" ? "active" : ""}`)}
                        onClicked={() => {
                            execAsync(["powerprofilesctl", "set", "performance"])
                            powerProfile.set("performance")
                        }}>
                        Performance
                    </button>
                </box>
            </box>

            {/* Display Settings */}
            <box className="display-section" vertical spacing={8}>
                <label className="section-label" label="Display Settings" />
                <box className="display-actions" spacing={6}>
                    <button className="action-button" onClicked={() => execAsync(["wdisplays"])}>
                        Display Configuration
                    </button>
                    <button className="action-button" onClicked={() => execAsync(["hyprctl", "dispatch", "exec", "hyprshade toggle"])}>
                        Night Light
                    </button>
                </box>
            </box>
        </box>
    }

    return <box className="power-display-compact">
        <icon icon="battery-symbolic" />
    </box>
}