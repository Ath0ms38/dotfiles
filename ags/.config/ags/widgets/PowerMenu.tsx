// ags/.config/ags/widgets/PowerMenu.tsx

import { execAsync } from "astal/process"
import { bind, Variable } from "astal"
import { Widget } from "astal/gtk3"
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
const username = Variable("user")

// Get username
execAsync(["whoami"]).then(out => username.set(out.trim())).catch(() => username.set("user"))

export default function PowerMenuWidget({ fullView = false }: { fullView?: boolean }) {
    if (fullView) {
        return new Widget.Box({
            className: "power-menu-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "🔌 Power Menu"
                }),
                
                bind(confirmAction).as(action => action ? 
                    // Confirmation dialog
                    new Widget.Box({
                        className: "confirmation-dialog",
                        vertical: true,
                        spacing: 12,
                        children: [
                            new Widget.Label({
                                className: "confirm-text",
                                label: `Are you sure you want to ${action.name.toLowerCase()}?`
                            }),
                            new Widget.Box({
                                spacing: 12,
                                halign: Gtk.Align.CENTER,
                                children: [
                                    new Widget.Button({
                                        className: "confirm-button",
                                        label: `Yes, ${action.name}`,
                                        onClicked: () => {
                                            execAsync(action.command)
                                            confirmAction.set(null)
                                        }
                                    }),
                                    new Widget.Button({
                                        className: "cancel-button",
                                        label: "Cancel",
                                        onClicked: () => confirmAction.set(null)
                                    })
                                ]
                            })
                        ]
                    }) : 
                    // Power actions grid
                    new Widget.Box({
                        className: "power-actions-grid",
                        vertical: true,
                        spacing: 12,
                        children: [
                            new Widget.Box({
                                spacing: 12,
                                children: powerActions.slice(0, 3).map(action => new Widget.Button({
                                    className: "power-action-button",
                                    onClicked: () => {
                                        if (action.confirm) {
                                            confirmAction.set(action)
                                        } else {
                                            execAsync(action.command)
                                        }
                                    },
                                    child: new Widget.Box({
                                        vertical: true,
                                        spacing: 8,
                                        children: [
                                            new Widget.Icon({ icon: action.icon, iconSize: 48 }),
                                            new Widget.Label({ label: action.name })
                                        ]
                                    })
                                }))
                            }),
                            new Widget.Box({
                                spacing: 12,
                                children: powerActions.slice(3).map(action => new Widget.Button({
                                    className: "power-action-button",
                                    onClicked: () => {
                                        if (action.confirm) {
                                            confirmAction.set(action)
                                        } else {
                                            execAsync(action.command)
                                        }
                                    },
                                    child: new Widget.Box({
                                        vertical: true,
                                        spacing: 8,
                                        children: [
                                            new Widget.Icon({ icon: action.icon, iconSize: 48 }),
                                            new Widget.Label({ label: action.name })
                                        ]
                                    })
                                }))
                            })
                        ]
                    })
                ),

                // User info
                new Widget.Box({
                    className: "user-info",
                    spacing: 8,
                    children: [
                        new Widget.Icon({ icon: "avatar-default-symbolic", iconSize: 24 }),
                        new Widget.Label({ label: bind(username) })
                    ]
                })
            ]
        })
    }

    return new Widget.Box({
        className: "power-menu-compact",
        children: [new Widget.Icon({ icon: "system-shutdown-symbolic" })]
    })
}
