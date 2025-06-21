// AGS v2 Main Application File

import { App, Astal, Gtk, Gdk } from "astal/gtk3"
import { Variable, bind } from "astal"

// Import all widgets
import AudioWidget from "./widgets/Audio"
import NetworkWidget from "./widgets/Network"
import SystemMonitorWidget from "./widgets/SystemMonitor"
import PowerDisplayWidget from "./widgets/PowerDisplay"
import MediaControlWidget from "./widgets/MediaControl"
import QuickSettingsWidget from "./widgets/QuickSettings"
import ProductivityWidget from "./widgets/Productivity"
import GamingWidget from "./widgets/Gaming"
import NotificationCenterWidget from "./widgets/NotificationCenter"
import PowerMenuWidget from "./widgets/PowerMenu"
import CalendarWidget from "./widgets/Calendar"

// Window visibility states for all widgets
const windowStates = {
    audio: Variable(false),
    network: Variable(false),
    system: Variable(false),
    powerDisplay: Variable(false),
    mediaControl: Variable(false),
    quickSettings: Variable(false),
    productivity: Variable(false),
    gaming: Variable(false),
    calendar: Variable(false),
    notifications: Variable(false),
    powerMenu: Variable(false)
}

// Function to close all popups
function closeAllPopups() {
    Object.values(windowStates).forEach(state => state.set(false))
}

// Audio popup window
function AudioPopup() {
    return <window
        name="audio-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.audio)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={400}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.audio.set(false)
            }
        }}>
        <AudioWidget fullView={true} />
    </window>
}

// Network popup window
function NetworkPopup() {
    return <window
        name="network-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.network)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={360}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.network.set(false)
            }
        }}>
        <NetworkWidget fullView={true} />
    </window>
}

// System Monitor popup window
function SystemMonitorPopup() {
    return <window
        name="system-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.system)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={320}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.system.set(false)
            }
        }}>
        <SystemMonitorWidget fullView={true} />
    </window>
}

// Power Display popup window
function PowerDisplayPopup() {
    return <window
        name="power-display-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.powerDisplay)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={280}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.powerDisplay.set(false)
            }
        }}>
        <PowerDisplayWidget fullView={true} />
    </window>
}

// Media Control popup window
function MediaControlPopup() {
    return <window
        name="media-control-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.mediaControl)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={240}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.mediaControl.set(false)
            }
        }}>
        <MediaControlWidget fullView={true} />
    </window>
}

// Quick Settings popup window
function QuickSettingsPopup() {
    return <window
        name="quick-settings-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.quickSettings)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={200}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.quickSettings.set(false)
            }
        }}>
        <QuickSettingsWidget fullView={true} />
    </window>
}

// Productivity popup window
function ProductivityPopup() {
    return <window
        name="productivity-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.productivity)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={160}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.productivity.set(false)
            }
        }}>
        <ProductivityWidget fullView={true} />
    </window>
}

// Gaming popup window
function GamingPopup() {
    return <window
        name="gaming-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.gaming)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={120}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.gaming.set(false)
            }
        }}>
        <GamingWidget fullView={true} />
    </window>
}

// Calendar popup window
function CalendarPopup() {
    return <window
        name="calendar-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.calendar)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={80}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.calendar.set(false)
            }
        }}>
        <CalendarWidget fullView={true} />
    </window>
}

// Notification popup window
function NotificationPopup() {
    return <window
        name="notification-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.notifications)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={40}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.notifications.set(false)
            }
        }}>
        <NotificationCenterWidget fullView={true} />
    </window>
}

// Power Menu popup window
function PowerMenuPopup() {
    return <window
        name="power-menu-popup"
        className="popup-window anime-room-theme"
        visible={bind(windowStates.powerMenu)}
        layer={Astal.Layer.OVERLAY}
        anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT}
        marginTop={50}
        marginRight={10}
        keymode={Astal.Keymode.ON_DEMAND}
        onKeyPressEvent={(_, event) => {
            if (event.get_keyval()[1] === Gdk.KEY_Escape) {
                windowStates.powerMenu.set(false)
            }
        }}>
        <PowerMenuWidget fullView={true} />
    </window>
}

App.start({
    css: "./style.css",
    requestHandler(request, res) {
        const [action, ...args] = request.split(' ')
        
        // Map of toggle actions to window states
        const toggleMap = {
            "toggle_audio": windowStates.audio,
            "toggle_network": windowStates.network,
            "toggle_system": windowStates.system,
            "toggle_power_display": windowStates.powerDisplay,
            "toggle_media_control": windowStates.mediaControl,
            "toggle_quick_settings": windowStates.quickSettings,
            "toggle_productivity": windowStates.productivity,
            "toggle_gaming": windowStates.gaming,
            "toggle_calendar": windowStates.calendar,
            "toggle_notifications": windowStates.notifications,
            "toggle_power_menu": windowStates.powerMenu
        }
        
        if (toggleMap[action]) {
            const currentState = toggleMap[action].get()
            // Close other popups first if opening
            if (!currentState) {
                closeAllPopups()
            }
            // Toggle the requested popup
            toggleMap[action].set(!currentState)
            res(`${action} ${toggleMap[action].get() ? 'shown' : 'hidden'}`)
        } else {
            res({ status: "error", message: "Unknown request" })
        }
    },
    main() {
        // Create all popup windows
        AudioPopup()
        NetworkPopup()
        SystemMonitorPopup()
        PowerDisplayPopup()
        MediaControlPopup()
        QuickSettingsPopup()
        ProductivityPopup()
        GamingPopup()
        CalendarPopup()
        NotificationPopup()
        PowerMenuPopup()
    }
})