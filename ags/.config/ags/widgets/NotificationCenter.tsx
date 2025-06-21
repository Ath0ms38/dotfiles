// AGS v2 Notification Center Widget

import Notifd from "gi://AstalNotifd"
import { bind, Variable } from "astal"
import { execAsync } from "astal/process"

const notificationFilters = {
    all: Variable(true),
    unread: Variable(false),
    today: Variable(false)
}

const dndEnabled = Variable(false)

export default function NotificationCenterWidget({ fullView = false }: { fullView?: boolean }) {
    const notifd = Notifd.get_default()

    if (fullView) {
        return <box className="notification-center-full" vertical spacing={12}>
            <box className="notification-header" spacing={12}>
                <label className="widget-title" label="🔔 Notification Center" />
                <box hexpand />
                <button className="clear-all-button"
                    onClicked={() => {
                        notifd.get_notifications().forEach(n => n.dismiss())
                        execAsync(["notify-send", "Notifications", "All notifications cleared"])
                    }}>
                    Clear All
                </button>
            </box>

            {/* DND Toggle */}
            <box className="dnd-section" spacing={12}>
                <label label="Do Not Disturb" />
                <box hexpand />
                <switch active={bind(dndEnabled)}
                    onActivate={({ active }) => {
                        dndEnabled.set(active)
                        execAsync(["swaync-client", active ? "-d" : "-D"])
                    }} />
            </box>

            {/* Filters */}
            <box className="filter-section" spacing={6}>
                <button className={bind(notificationFilters.all).as(active => `filter-button ${active ? "active" : ""}`)}
                    onClicked={() => {
                        Object.values(notificationFilters).forEach(f => f.set(false))
                        notificationFilters.all.set(true)
                    }}>
                    All
                </button>
                <button className={bind(notificationFilters.unread).as(active => `filter-button ${active ? "active" : ""}`)}
                    onClicked={() => {
                        Object.values(notificationFilters).forEach(f => f.set(false))
                        notificationFilters.unread.set(true)
                    }}>
                    Unread
                </button>
                <button className={bind(notificationFilters.today).as(active => `filter-button ${active ? "active" : ""}`)}
                    onClicked={() => {
                        Object.values(notificationFilters).forEach(f => f.set(false))
                        notificationFilters.today.set(true)
                    }}>
                    Today
                </button>
            </box>

            {/* Notifications List */}
            <scrollable heightRequest={400}>
                <box className="notification-list" vertical spacing={6}>
                    {bind(notifd, "notifications").as(notifications => {
                        // Filter notifications based on active filter
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
                        
                        return filtered.length === 0 ? (
                            <label className="no-notifications" label="No notifications" />
                        ) : (
                            filtered.map(notification => (
                                <box key={notification.id} className="notification-item" vertical spacing={6}>
                                    <box spacing={8}>
                                        {notification.appIcon && (
                                            <icon icon={notification.appIcon} iconSize={24} />
                                        )}
                                        <box vertical hexpand>
                                            <box>
                                                <label className="notification-app" label={notification.appName} />
                                                <box hexpand />
                                                <label className="notification-time" 
                                                    label={new Date(notification.time * 1000).toLocaleTimeString('fr-FR', {
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    })} />
                                            </box>
                                            <label className="notification-summary" label={notification.summary} />
                                            <label className="notification-body" label={notification.body} />
                                        </box>
                                        <button className="dismiss-button"
                                            onClicked={() => notification.dismiss()}>
                                            <icon icon="window-close-symbolic" />
                                        </button>
                                    </box>
                                    
                                    {/* Action buttons */}
                                    {notification.actions.length > 0 && (
                                        <box className="notification-actions" spacing={6}>
                                            {notification.actions.map(action => (
                                                <button key={action.id} className="action-button"
                                                    onClicked={() => notification.invoke(action.id)}>
                                                    {action.label}
                                                </button>
                                            ))}
                                        </box>
                                    )}
                                </box>
                            ))
                        )
                    })}
                </box>
            </scrollable>

            {/* Settings */}
            <button className="settings-button" 
                onClicked={() => execAsync(["swaync-client", "-sw"])}>
                Notification Settings
            </button>
        </box>
    }

    const notificationCount = bind(notifd, "notifications").as(n => n.length)

    return <box className="notification-center-compact">
        <icon icon="notification-symbolic" />
        {bind(notificationCount).as(count => count > 0 && (
            <label className="notification-badge" label={count.toString()} />
        ))}
    </box>
}