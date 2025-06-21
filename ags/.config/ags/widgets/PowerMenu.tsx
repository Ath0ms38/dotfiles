// AGS v2 Power Menu Widget

import { execAsync } from "astal/process"
import { bind } from "astal"
import { Variable } from "astal"
import Gtk from "gi://Gtk?version=3.0"

interface PowerAction {
    name: string
    icon: string
    command: string[]
    confirm: boolean
}

const powerActions: PowerAction[] = [
    { name: "Lock", icon: "system-lock-screen-symbolic", command: ["hyprlock"], confirm: false },
    { name: "Logout", icon: "system-log-out-symbolic", command: ["hyprctl", "dispatch", "exit"], confirm: true },
    { name: "Sleep", icon: "weather-clear-night-symbolic", command: ["systemctl", "suspend"], confirm: false },
    { name: "Hibernate", icon: "drive-harddisk-symbolic", command: ["systemctl", "hibernate"], confirm: true },
    { name: "Reboot", icon: "system-reboot-symbolic", command: ["systemctl", "reboot"], confirm: true },
    { name: "Shutdown", icon: "system-shutdown-symbolic", command: ["systemctl", "poweroff"], confirm: true }
]

const confirmAction = Variable<PowerAction | null>(null)

export default function PowerMenuWidget({ fullView = false }: { fullView?: boolean }) {
    if (fullView) {
        return <box className="power-menu-full" vertical spacing={12}>
            <label className="widget-title" label="🔌 Power Menu" />
            
            {bind(confirmAction).as(action => action ? (
                // Confirmation dialog
                <box className="confirmation-dialog" vertical spacing={12}>
                    <label className="confirm-text" 
                        label={`Are you sure you want to ${action.name.toLowerCase()}?`} />
                    <box spacing={12} halign={Gtk.Align.CENTER}>
                        <button className="confirm-button"
                            onClicked={() => {
                                execAsync(action.command)
                                confirmAction.set(null)
                            }}>
                            Yes, {action.name}
                        </button>
                        <button className="cancel-button"
                            onClicked={() => confirmAction.set(null)}>
                            Cancel
                        </button>
                    </box>
                </box>
            ) : (
                // Power actions grid
                <box className="power-actions-grid" vertical spacing={12}>
                    <box spacing={12}>
                        {powerActions.slice(0, 3).map(action => (
                            <button key={action.name} className="power-action-button"
                                onClicked={() => {
                                    if (action.confirm) {
                                        confirmAction.set(action)
                                    } else {
                                        execAsync(action.command)
                                    }
                                }}>
                                <box vertical spacing={8}>
                                    <icon icon={action.icon} iconSize={48} />
                                    <label label={action.name} />
                                </box>
                            </button>
                        ))}
                    </box>
                    <box spacing={12}>
                        {powerActions.slice(3).map(action => (
                            <button key={action.name} className="power-action-button"
                                onClicked={() => {
                                    if (action.confirm) {
                                        confirmAction.set(action)
                                    } else {
                                        execAsync(action.command)
                                    }
                                }}>
                                <box vertical spacing={8}>
                                    <icon icon={action.icon} iconSize={48} />
                                    <label label={action.name} />
                                </box>
                            </button>
                        ))}
                    </box>
                </box>
            ))}

            {/* User info */}
            <box className="user-info" spacing={8}>
                <icon icon="avatar-default-symbolic" iconSize={24} />
                <label label={execAsync(["whoami"]).then(out => out.trim()).catch(() => "user")} />
            </box>
        </box>
    }

    return <box className="power-menu-compact">
        <icon icon="system-shutdown-symbolic" />
    </box>
}