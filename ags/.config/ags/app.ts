#!/usr/bin/env -S ags run

import { App } from "astal/gtk3"
import { exec, execAsync } from "astal/process"
import { Variable, bind } from "astal"

// Import widgets with error handling
const loadWidget = (name: string) => {
    try {
        return require(`./widgets/${name}`).default
    } catch (e) {
        console.error(`Failed to load widget ${name}:`, e)
        return null
    }
}

// Load all widgets
const AudioWidget = loadWidget("Audio")
const NetworkWidget = loadWidget("Network")
const SystemMonitorWidget = loadWidget("SystemMonitor")
const PowerDisplayWidget = loadWidget("PowerDisplay")
const MediaControlWidget = loadWidget("MediaControl")
const QuickSettingsWidget = loadWidget("QuickSettings")
const ProductivityWidget = loadWidget("Productivity")
const GamingWidget = loadWidget("Gaming")
const NotificationCenterWidget = loadWidget("NotificationCenter")
const PowerMenuWidget = loadWidget("PowerMenu")
const CalendarWidget = loadWidget("Calendar")

// State management
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

// Close all popups
function closeAllPopups() {
    Object.values(windowStates).forEach(state => state.set(false))
}

// Create popup window factory
function createPopupWindow(name: string, Widget: any, state: Variable<boolean>, position: { marginTop: number, marginRight: number }) {
    if (!Widget) return null
    
    return App.window({
        name: `${name}-popup`,
        className: "popup-window anime-room-theme",
        visible: bind(state),
        layer: "overlay",
        anchor: ["top", "right"],
        marginTop: position.marginTop,
        marginRight: position.marginRight,
        keymode: "on-demand",
        setup: (self) => {
            self.on("key-press-event", (_, event) => {
                if (event.get_keyval()[1] === 65307) { // Escape key
                    state.set(false)
                }
            })
        },
        child: Widget({ fullView: true })
    })
}

// Main application
App.start({
    css: `${App.configDir}/style.css`,
    
    requestHandler(request: string, res: (response: any) => void) {
        const [action, ...args] = request.split(' ')
        
        const toggleMap: Record<string, Variable<boolean>> = {
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
            if (!currentState) {
                closeAllPopups()
            }
            toggleMap[action].set(!currentState)
            res(`${action} ${toggleMap[action].get() ? 'shown' : 'hidden'}`)
        } else {
            res({ status: "error", message: "Unknown request" })
        }
    },
    
    main() {
        // Create all popup windows with error handling
        const positions = {
            audio: { marginTop: 50, marginRight: 400 },
            network: { marginTop: 50, marginRight: 360 },
            system: { marginTop: 50, marginRight: 320 },
            powerDisplay: { marginTop: 50, marginRight: 280 },
            mediaControl: { marginTop: 50, marginRight: 240 },
            quickSettings: { marginTop: 50, marginRight: 200 },
            productivity: { marginTop: 50, marginRight: 160 },
            gaming: { marginTop: 50, marginRight: 120 },
            calendar: { marginTop: 50, marginRight: 80 },
            notifications: { marginTop: 50, marginRight: 40 },
            powerMenu: { marginTop: 50, marginRight: 10 }
        }
        
        if (AudioWidget) createPopupWindow("audio", AudioWidget, windowStates.audio, positions.audio)
        if (NetworkWidget) createPopupWindow("network", NetworkWidget, windowStates.network, positions.network)
        if (SystemMonitorWidget) createPopupWindow("system", SystemMonitorWidget, windowStates.system, positions.system)
        if (PowerDisplayWidget) createPopupWindow("power-display", PowerDisplayWidget, windowStates.powerDisplay, positions.powerDisplay)
        if (MediaControlWidget) createPopupWindow("media-control", MediaControlWidget, windowStates.mediaControl, positions.mediaControl)
        if (QuickSettingsWidget) createPopupWindow("quick-settings", QuickSettingsWidget, windowStates.quickSettings, positions.quickSettings)
        if (ProductivityWidget) createPopupWindow("productivity", ProductivityWidget, windowStates.productivity, positions.productivity)
        if (GamingWidget) createPopupWindow("gaming", GamingWidget, windowStates.gaming, positions.gaming)
        if (CalendarWidget) createPopupWindow("calendar", CalendarWidget, windowStates.calendar, positions.calendar)
        if (NotificationCenterWidget) createPopupWindow("notifications", NotificationCenterWidget, windowStates.notifications, positions.notifications)
        if (PowerMenuWidget) createPopupWindow("power-menu", PowerMenuWidget, windowStates.powerMenu, positions.powerMenu)
    }
})