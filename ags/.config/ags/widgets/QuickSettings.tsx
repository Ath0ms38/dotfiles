// AGS v2 Quick Settings Widget

import { Variable, bind } from "astal"
import Network from "gi://AstalNetwork"
import Bluetooth from "gi://AstalBluetooth"
import { execAsync } from "astal/process"

const dndEnabled = Variable(false)
const nightLightEnabled = Variable(false)
const airplaneModeEnabled = Variable(false)

export default function QuickSettingsWidget({ fullView = false }: { fullView?: boolean }) {
    const network = Network.get_default()
    const bluetooth = Bluetooth.get_default()

    if (fullView) {
        return <box className="quick-settings-full" vertical spacing={12}>
            <label className="widget-title" label="⚡ Quick Settings" />
            
            {/* Toggle grid */}
            <box className="toggle-grid" vertical spacing={8}>
                <box spacing={8}>
                    <button className={bind(network.wifi, "enabled").as(e => `toggle-button ${e ? "active" : ""}`)}
                        onClicked={() => network.wifi && (network.wifi.enabled = !network.wifi.enabled)}>
                        <box vertical spacing={4}>
                            <icon icon="network-wireless-symbolic" iconSize={24} />
                            <label label="WiFi" />
                        </box>
                    </button>
                    
                    <button className={bind(bluetooth, "isPowered").as(p => `toggle-button ${p ? "active" : ""}`)}
                        onClicked={() => bluetooth.adapter?.setPowered(!bluetooth.isPowered)}>
                        <box vertical spacing={4}>
                            <icon icon="bluetooth-symbolic" iconSize={24} />
                            <label label="Bluetooth" />
                        </box>
                    </button>
                    
                    <button className={bind(dndEnabled).as(e => `toggle-button ${e ? "active" : ""}`)}
                        onClicked={() => {
                            dndEnabled.set(!dndEnabled.get())
                            execAsync(["swaync-client", "-d"])
                        }}>
                        <box vertical spacing={4}>
                            <icon icon="dialog-information-symbolic" iconSize={24} />
                            <label label="Do Not Disturb" />
                        </box>
                    </button>
                </box>
                
                <box spacing={8}>
                    <button className={bind(nightLightEnabled).as(e => `toggle-button ${e ? "active" : ""}`)}
                        onClicked={() => {
                            nightLightEnabled.set(!nightLightEnabled.get())
                            execAsync(["hyprshade", "toggle"])
                        }}>
                        <box vertical spacing={4}>
                            <icon icon="night-light-symbolic" iconSize={24} />
                            <label label="Night Light" />
                        </box>
                    </button>
                    
                    <button className={bind(airplaneModeEnabled).as(e => `toggle-button ${e ? "active" : ""}`)}
                        onClicked={() => {
                            airplaneModeEnabled.set(!airplaneModeEnabled.get())
                            if (airplaneModeEnabled.get()) {
                                network.wifi && (network.wifi.enabled = false)
                                bluetooth.adapter?.setPowered(false)
                            } else {
                                network.wifi && (network.wifi.enabled = true)
                                bluetooth.adapter?.setPowered(true)
                            }
                        }}>
                        <box vertical spacing={4}>
                            <icon icon="airplane-mode-symbolic" iconSize={24} />
                            <label label="Airplane Mode" />
                        </box>
                    </button>
                    
                    <button className="toggle-button"
                        onClicked={() => execAsync(["hyprpicker", "-a"])}>
                        <box vertical spacing={4}>
                            <icon icon="applications-graphics-symbolic" iconSize={24} />
                            <label label="Color Picker" />
                        </box>
                    </button>
                </box>
            </box>

            {/* Screenshot tools */}
            <box className="screenshot-section" vertical spacing={8}>
                <label className="section-label" label="Screenshot" />
                <box spacing={6}>
                    <button className="action-button" onClicked={() => execAsync(["grimblast", "copy", "area"])}>
                        Area
                    </button>
                    <button className="action-button" onClicked={() => execAsync(["grimblast", "copy", "active"])}>
                        Window
                    </button>
                    <button className="action-button" onClicked={() => execAsync(["grimblast", "copy", "screen"])}>
                        Full Screen
                    </button>
                </box>
            </box>

            {/* Screen recording */}
            <box className="recording-section" vertical spacing={8}>
                <label className="section-label" label="Screen Recording" />
                <button className="record-button" onClicked={() => execAsync(["wf-recorder", "-g", "$(slurp)"])}>
                    Start Recording
                </button>
            </box>

            {/* System services */}
            <box className="services-section" vertical spacing={8}>
                <label className="section-label" label="System Services" />
                <box spacing={6}>
                    <button className="action-button" onClicked={() => execAsync(["systemctl", "--user", "restart", "waybar"])}>
                        Restart Waybar
                    </button>
                    <button className="action-button" onClicked={() => execAsync(["hyprctl", "reload"])}>
                        Reload Hyprland
                    </button>
                </box>
            </box>
        </box>
    }

    return <box className="quick-settings-compact">
        <icon icon="emblem-system-symbolic" />
    </box>
}