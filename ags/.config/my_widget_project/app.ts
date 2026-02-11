import app from "ags/gtk4/app"
import { AudioWidget } from "./widget/Audio"
import { NetworkWidget } from "./widget/Network"
import { SystemMonitorWidget } from "./widget/SystemMonitor"
import { PowerDisplayWidget } from "./widget/PowerDisplay"
import { MediaControlWidget } from "./widget/MediaControl"
import { QuickSettingsWidget } from "./widget/QuickSettings"
import { ProductivityWidget } from "./widget/Productivity"
import { GamingWidget } from "./widget/Gaming"
import { NotificationCenterWidget } from "./widget/NotificationCenter"
import { PowerMenuWidget } from "./widget/PowerMenu"

// Store windows for managing visibility
const windows: { [key: string]: any } = {}

// Hide all widgets
function hideAllWidgets() {
  Object.values(windows).forEach((window) => {
    window.visible = false
  })
}

// Apply custom CSS/SCSS styling
const customCSS = `
/* === KITTY & WAYBAR THEME COLORS === */
:root {
  --primary-bg: rgba(61, 47, 42, 0.92);
  --primary-text: #f5f0e8;
  --accent-brown: #8d6e63;
  --accent-gold: #ffcc5c;
  --accent-pink: #ffb7ba;
  --accent-magenta: #fd79a8;
  --accent-blue: #74b9ff;
  --bright-white: #ffffff;
  --black: #2d2a2e;
}

* {
  font-family: "JetBrainsMono Nerd Font", "JetBrainsMono", "FiraCode Nerd Font", monospace;
  font-size: 12px;
  font-weight: 600;
}

window {
  background: transparent;
  color: var(--primary-text);
}

.AudioWidget {
  background: 
    linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02)),
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.1), transparent 50%),
    rgba(120, 95, 85, 0.8);
  color: var(--primary-text);
  border-radius: 10px;
  border: 2px solid var(--accent-pink);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 2px rgba(255, 255, 255, 0.3),
    inset 0 -1px 2px rgba(0, 0, 0, 0.2);
  padding: 0;
}

.AudioWidget scrolledwindow {
  padding: 12px;
}

.NetworkWidget,
.SystemMonitorWidget,
.PowerDisplayWidget,
.MediaControlWidget,
.QuickSettingsWidget,
.ProductivityWidget,
.GamingWidget,
.NotificationCenterWidget,
.PowerMenuWidget {
  background: 
    linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02)),
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.1), transparent 50%),
    rgba(120, 95, 85, 0.8);
  color: var(--primary-text);
  border-radius: 10px;
  border: 2px solid var(--accent-pink);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 2px rgba(255, 255, 255, 0.3),
    inset 0 -1px 2px rgba(0, 0, 0, 0.2);
  padding: 12px;
  min-width: 350px;
  min-height: 200px;
}

box {
  background: transparent;
  color: var(--primary-text);
}

label:first-child {
  font-size: 14px;
  font-weight: bold;
  color: var(--accent-gold);
  margin-bottom: 10px;
  padding: 4px 0;
}

label {
  color: var(--primary-text);
  padding: 4px 0;
  margin: 2px 0;
  font-weight: 500;
  font-size: 12px;
}

button {
  border-radius: 6px;
  padding: 8px 12px;
  margin: 4px 2px;
  background: var(--accent-brown);
  color: var(--primary-text);
  border: 1px solid transparent;
  transition: all 0.2s ease-out;
  min-height: 22px;
  min-width: 50px;
  font-size: 12px;
  font-weight: 600;
}

button:hover {
  background: var(--accent-pink);
  color: var(--black);
  border: 1px solid var(--accent-pink);
  box-shadow: 0 0 0 2px var(--accent-pink);
}

button:active {
  background: var(--accent-gold);
  color: var(--black);
  box-shadow: 0 0 0 2px var(--accent-gold);
}

togglebutton {
  border-radius: 6px;
  padding: 8px 12px;
  margin: 4px 2px;
  background: var(--accent-brown);
  color: var(--primary-text);
  border: 1px solid transparent;
  transition: all 0.2s ease-out;
  min-height: 22px;
  min-width: 50px;
  font-size: 12px;
  font-weight: 600;
}

togglebutton:hover {
  background: var(--accent-pink);
  color: var(--black);
  border: 1px solid var(--accent-pink);
  box-shadow: 0 0 0 2px var(--accent-pink);
}

togglebutton:checked {
  background: var(--accent-blue);
  color: var(--bright-white);
  border: 1px solid var(--accent-blue);
  box-shadow: 0 0 0 2px var(--accent-blue);
  animation: pulse 1.5s ease-in-out infinite;
}

togglebutton:checked:hover {
  background: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--accent-blue);
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.85; }
  100% { opacity: 1; }
}

scrolledwindow {
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.15);
}

scrolledwindow label {
  padding: 4px 4px;
}

/* Audio Widget Specific Styling */
.AudioWidget label.title {
  font-size: 16px;
  font-weight: bold;
  color: var(--accent-gold);
  margin-bottom: 8px;
}

.AudioWidget label.device-label {
  font-size: 11px;
  color: var(--accent-blue);
  margin-top: 4px;
}

.AudioWidget label.app-title {
  font-size: 13px;
  font-weight: bold;
  color: var(--accent-gold);
  margin-top: 8px;
  margin-bottom: 4px;
}

.AudioWidget label.no-apps-label {
  font-size: 11px;
  color: var(--bright-black);
  font-style: italic;
  padding: 8px;
}

.AudioWidget box.app-control {
  padding: 4px 0;
  margin: 2px 0;
}

.AudioWidget button.app-group-button {
  border-radius: 6px;
  padding: 8px 12px;
  margin: 4px 0;
  background: var(--accent-brown);
  color: var(--primary-text);
  border: 1px solid transparent;
  transition: all 0.2s ease-out;
  min-height: 24px;
  font-size: 12px;
  font-weight: 600;
}

.AudioWidget button.app-group-button:hover {
  background: var(--accent-pink);
  color: var(--black);
  border: 1px solid var(--accent-pink);
  box-shadow: 0 0 0 2px var(--accent-pink);
}

.AudioWidget button.app-group-button:checked {
  background: var(--accent-blue);
  color: var(--bright-white);
  border: 1px solid var(--accent-blue);
}

.AudioWidget box.app-group {
  padding: 4px 0;
  margin: 4px 0;
}

.AudioWidget box.app-window {
  padding: 4px 0;
  margin: 2px 0;
}

.AudioWidget button.audio-button {
  border-radius: 6px;
  padding: 8px 12px;
  margin: 4px 0;
  background: var(--accent-brown);
  color: var(--primary-text);
  border: 1px solid transparent;
  transition: all 0.2s ease-out;
  min-height: 24px;
  font-size: 12px;
  font-weight: 600;
}

.AudioWidget button.audio-button:hover {
  background: var(--accent-pink);
  color: var(--black);
  border: 1px solid var(--accent-pink);
  box-shadow: 0 0 0 2px var(--accent-pink);
}

.AudioWidget button.audio-button:active {
  background: var(--accent-gold);
  color: var(--black);
  box-shadow: 0 0 0 2px var(--accent-gold);
}

scale {
  min-height: 24px;
}
`

app.start({
  css: customCSS,
  requestHandler(argv: string[], res: (response: any) => void) {
    const request = argv.join(" ")
    // Handle toggle requests from waybar
    const windowMap: { [key: string]: string } = {
      toggle_audio: "audio",
      toggle_network: "network",
      toggle_system: "system",
      toggle_power_display: "power_display",
      toggle_media_control: "media_control",
      toggle_quick_settings: "quick_settings",
      toggle_productivity: "productivity",
      toggle_gaming: "gaming",
      toggle_notifications: "notifications",
      toggle_power_menu: "power_menu",
    }

    if (request in windowMap) {
      const windowName = windowMap[request]
      const window = windows[windowName]
      if (window) {
        // If already visible, hide it; otherwise hide all and show this one
        if (window.visible) {
          window.visible = false
        } else {
          hideAllWidgets()
          window.visible = true
        }
        res(`Toggled ${windowName}`)
      } else {
        res(`Window ${windowName} not found`)
      }
    } else {
      res("unknown command")
    }
  },
  main() {
    // Create all widget windows
    windows["audio"] = AudioWidget()
    windows["network"] = NetworkWidget()
    windows["system"] = SystemMonitorWidget()
    windows["power_display"] = PowerDisplayWidget()
    windows["media_control"] = MediaControlWidget()
    windows["quick_settings"] = QuickSettingsWidget()
    windows["productivity"] = ProductivityWidget()
    windows["gaming"] = GamingWidget()
    windows["notifications"] = NotificationCenterWidget()
    windows["power_menu"] = PowerMenuWidget()

    Object.values(windows).forEach((window) => {
      app.add_window(window)
    })
  },
})
