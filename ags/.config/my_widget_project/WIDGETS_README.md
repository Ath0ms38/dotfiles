# AGS Waybar Widgets

This is a set of AGS widgets designed to integrate with your waybar configuration. Each widget can be toggled from waybar custom button clicks.

## Widgets Created

1. **Audio Widget** - Volume control and device management
2. **Network Widget** - WiFi, Ethernet, and Bluetooth controls
3. **System Monitor Widget** - CPU and Memory usage display
4. **Power Display Widget** - Battery status and time remaining
5. **Media Control Widget** - Media player controls (Previous, Play/Pause, Next)
6. **Quick Settings Widget** - Toggle Dark Mode, Bluetooth, and WiFi
7. **Productivity Widget** - Active time, Focus Mode, and Do Not Disturb
8. **Gaming Widget** - Performance Mode, notification disable, and boost settings
9. **Notification Center Widget** - Display notifications with clear all option
10. **Power Menu Widget** - Sleep, Restart, and Shutdown buttons

## How It Works

Each widget is a toggleable window that opens and closes via AGS request commands from waybar. The command format is:

```bash
ags request toggle_<widget_name>
```

### Example Waybar Configuration

Your `waybar/config.jsonc` already has the custom modules configured:

```jsonc
"custom/ags-audio": {
  "format": "",
  "tooltip": "Audio",
  "on-click": "ags request toggle_audio"
}
```

When you click on the button in waybar, it sends a request to AGS to toggle the corresponding widget window.

## Running the Application

From the `ags/.config/my_widget_project/` directory:

```bash
# Run in development mode
ags run

# Or build and run
ags build
ags run ./out/main.js
```

## Theme

The widgets use the same **Anime Room aesthetic** as your waybar configuration with:

- **Primary Colors**: Warm browns, pinks, golds, and purples
- **Background**: Semi-transparent warm brown (#3d2d29)
- **Text**: Warm off-white (#f5f0e8)
- **Accents**: 
  - Brown: `rgba(141, 110, 99, 0.85)`
  - Pink: `rgba(255, 183, 186, 0.6)` - Hover states
  - Gold: `rgba(255, 204, 92, 0.8)` - Active states
  - Purple: `rgba(179, 157, 219, 0.9)` - Toggle active state

### Animations

- **Pulse**: Smooth opacity animation (2s)
- **Border Shift**: Pink border animation (6s)

## Keyboard Shortcuts

- **ESC**: Close any open widget window

## File Structure

```
ags/.config/my_widget_project/
├── app.ts                    # Main entry point
├── style.scss                # Themed styles
├── package.json
├── tsconfig.json
├── env.d.ts
└── widget/
    ├── Audio.ts
    ├── Network.ts
    ├── SystemMonitor.ts
    ├── PowerDisplay.ts
    ├── MediaControl.ts
    ├── QuickSettings.ts
    ├── Productivity.ts
    ├── Gaming.ts
    ├── NotificationCenter.ts
    └── PowerMenu.ts
```

## Extending the Widgets

Each widget file exports a function that returns an `Astal.Window`. You can customize:

1. **Content**: Add labels, buttons, toggles to match your system
2. **Window Properties**: Position, size, animation behavior
3. **Event Handlers**: Add `on-click` handlers to buttons
4. **Styling**: Modify CSS classes in `style.scss`

Example: Customizing the Audio widget to show volume:

```typescript
// In widget/Audio.ts
const volumeLabel = new Gtk.Label({
  label: "Volume: 75%",
})
box.append(volumeLabel)
```

## Integration with System Services

To make these widgets functional with actual system data (audio, network, battery), import Astal libraries:

```typescript
import AstalBattery from "gi://AstalBattery?version=0.1"
import AstalNetwork from "gi://AstalNetwork?version=0.1"
import AstalAudio from "gi://AstalAudio?version=0.1"

const battery = AstalBattery.get_default()
const network = AstalNetwork.get_default()
const audio = AstalAudio.get_default()
```

Then use `createBinding` to bind widget labels to system properties:

```typescript
import { createBinding } from "ags"

const batteryLabel = new Gtk.Label({
  label: createBinding(battery, "percentage").as(p => `Battery: ${p}%`)
})
```

## Tips

- All widgets automatically close with ESC key
- Widgets appear in the top-right corner by default
- Multiple widgets can be open simultaneously
- The request handler in `app.ts` can be extended with additional commands

Enjoy your AGS widgets integrated with waybar!
