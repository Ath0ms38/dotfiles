// ags/.config/ags/widgets/NotificationCenter.tsx

import Notifd from "gi://AstalNotifd"
import { bind, Variable } from "astal"
import { execAsync } from "astal/process"
import { Widget } from "astal/gtk3"

const notificationFilters = {
    all: Variable(true),
    unread: Variable(false),
    today: Variable(false)
}

const dndEnabled = Variable(false)

export default function NotificationCenterWidget({ fullView = false }: { fullView?: boolean }) {
    const notifd = Notifd.get_default()

    if (fullView) {
        return new Widget.Box({
            className: "notification-center-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Box({
                    className: "notification-header",
                    spacing: 12,
                    children: [
                        new Widget.Label({
                            className: "widget-title",
                            label: "🔔 Notification Center"
                        }),
                        new Widget.Box({ hexpand: true }),
                        new Widget.Button({
                            className: "clear-all-button",
                            label: "Clear All",
                            onClicked: () => {
                                notifd.get_notifications().forEach(n => n.dismiss())
                                execAsync(["notify-send", "Notifications", "All notifications cleared"])
                            }
                        })
                    ]
                }),

                // DND Toggle
                new Widget.Box({
                    className: "dnd-section",
                    spacing: 12,
                    children: [
                        new Widget.Label({ label: "Do Not Disturb" }),
                        new Widget.Box({ hexpand: true }),
                        // @ts-ignore - Switch widget
                        new Widget.Switch({
                            active: bind(dndEnabled),
                            onActivate: ({ active }: any) => {
                                dndEnabled.set(active)
                                execAsync(["swaync-client", active ? "-d" : "-D"])
                            }
                        })
                    ]
                }),

                // Filters
                new Widget.Box({
                    className: "filter-section",
                    spacing: 6,
                    children: [
                        new Widget.Button({
                            className: bind(notificationFilters.all).as(active => `filter-button ${active ? "active" : ""}`),
                            label: "All",
                            onClicked: () => {
                                Object.values(notificationFilters).forEach(f => f.set(false))
                                notificationFilters.all.set(true)
                            }
                        }),
                        new Widget.Button({
                            className: bind(notificationFilters.unread).as(active => `filter-button ${active ? "active" : ""}`),
                            label: "Unread",
                            onClicked: () => {
                                Object.values(notificationFilters).forEach(f => f.set(false))
                                notificationFilters.unread.set(true)
                            }
                        }),
                        new Widget.Button({
                            className: bind(notificationFilters.today).as(active => `filter-button ${active ? "active" : ""}`),
                            label: "Today",
                            onClicked: () => {
                                Object.values(notificationFilters).forEach(f => f.set(false))
                                notificationFilters.today.set(true)
                            }
                        })
                    ]
                }),

                // Notifications List
                // @ts-ignore - Scrollable widget
                new Widget.Scrollable({
                    heightRequest: 400,
                    child: new Widget.Box({
                        className: "notification-list",
                        vertical: true,
                        spacing: 6,
                        children: bind(notifd, "notifications").as(notifications => {
                            let filtered = notifications
                            
                            if (notificationFilters.unread.get()) {
                                filtered = filtered.filter(n => !n.read)
                            } else if (notificationFilters.today.get()) {
                                const today = new Date()
                                today.setHours(0, 0, 0, 0)
                                filtered = filtered.filter(n => {
                                    const notifDate = new Date(n.time * 1000)
                                    return notifDate >= today
                                })
                            }
                            
                            return filtered.length === 0 ? [
                                new Widget.Label({
                                    className: "no-notifications",
                                    label: "No notifications"
                                })
                            ] : filtered.map(notification => new Widget.Box({
                                className: "notification-item",
                                vertical: true,
                                spacing: 6,
                                children: [
                                    new Widget.Box({
                                        spacing: 8,
                                        children: [
                                            notification.appIcon ? new Widget.Icon({
                                                icon: notification.appIcon,
                                                iconSize: 24
                                            }) : new Widget.Box({}),
                                            new Widget.Box({
                                                vertical: true,
                                                hexpand: true,
                                                children: [
                                                    new Widget.Box({
                                                        children: [
                                                            new Widget.Label({
                                                                className: "notification-app",
                                                                label: notification.appName
                                                            }),
                                                            new Widget.Box({ hexpand: true }),
                                                            new Widget.Label({
                                                                className: "notification-time",
                                                                label: new Date(notification.time * 1000).toLocaleTimeString('fr-FR', {
                                                                    hour: '2-digit',
                                                                    minute: '2-digit'
                                                                })
                                                            })
                                                        ]
                                                    }),
                                                    new Widget.Label({
                                                        className: "notification-summary",
                                                        label: notification.summary
                                                    }),
                                                    new Widget.Label({
                                                        className: "notification-body",
                                                        label: notification.body
                                                    })
                                                ]
                                            }),
                                            new Widget.Button({
                                                className: "dismiss-button",
                                                onClicked: () => notification.dismiss(),
                                                child: new Widget.Icon({ icon: "window-close-symbolic" })
                                            })
                                        ]
                                    }),
                                    
                                    notification.actions.length > 0 ? new Widget.Box({
                                        className: "notification-actions",
                                        spacing: 6,
                                        children: notification.actions.map(action => new Widget.Button({
                                            className: "action-button",
                                            label: action.label,
                                            onClicked: () => notification.invoke(action.id)
                                        }))
                                    }) : new Widget.Box({})
                                ]
                            }))
                        })
                    })
                }),

                // Settings
                new Widget.Button({
                    className: "settings-button",
                    label: "Notification Settings",
                    onClicked: () => execAsync(["swaync-client", "-sw"])
                })
            ]
        })
    }

    const notificationCount = bind(notifd, "notifications").as(n => n.length)

    return new Widget.Box({
        className: "notification-center-compact",
        children: [
            new Widget.Icon({ icon: "notification-symbolic" }),
            bind(notificationCount).as(count => count > 0 ? new Widget.Label({
                className: "notification-badge",
                label: count.toString()
            }) : new Widget.Box({}))
        ]
    })
}
