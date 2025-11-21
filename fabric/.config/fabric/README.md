# Fabric Bar - Custom Waybar Replacement

A Python-based status bar and widget system for Hyprland using the Fabric framework, designed to replace your waybar + ags setup with a cleaner, more maintainable solution.

## Features

### Main Bar
- **Workspace Management**: Hyprland workspaces 1-10 with visual indicators
- **Special Workspace Buttons**:
  - Discord (workspace 11) - 󰙯
  - VS Code (workspace 12) - 󰨞
  - Minecraft (workspace 13) - 󰍳
  - Steam (workspace 14) - 󰓓
- **Active Window Display**: Shows current window title
- **Clock**: Multi-format time/date display
- **Widget Triggers**: Quick access buttons for all widgets

### Popup Widgets

#### 🔊 Audio Control
- Speaker volume control with sliders
- Microphone volume control
- Per-application volume mixing
- Mute toggles for all streams
- Real-time audio updates

#### 󰀂 Network & Bluetooth
- WiFi network scanner and connector
- Signal strength indicators
- Bluetooth device manager
- Connect/disconnect controls
- Real-time scanning

#### 󰁹 Battery & Power
- Battery percentage and status
- Time remaining estimation
- Power profile switcher (Performance/Balanced/Power Saver)
- Visual battery indicators

#### ⏻ Power Menu
- Shutdown
- Reboot
- Logout (Hyprland exit)
- Lock screen
- Sleep/Suspend

####  System Tray
- Display system tray icons
- Click to activate applications
- Automatic updates

####  Utilities
- Live clock with date and week number
- Note taking with timestamps
- Todo/Reminder list with completion tracking
- Persistent storage

### Styling
- Warm anime room aesthetic
- Animated hover effects
- Smooth transitions
- Custom colors for each app workspace
- Rounded corners and soft shadows

## Installation

### 1. Install Dependencies

The setup script will install all required dependencies. Just run:

```bash
cd ~/.config/fabric  # or wherever you cloned this
./setup.sh
```

This will:
- Install system packages (GTK3, Cairo, Python, etc.)
- Create a Python virtual environment
- Install Fabric from GitHub
- Install additional Python dependencies (psutil)

### 2. Manual Installation (if setup script fails)

Install system dependencies:
```bash
sudo pacman -S --needed python python-pip python-gobject python-cairo python-loguru \
    gtk3 cairo gtk-layer-shell libgirepository gobject-introspection \
    gobject-introspection-runtime pkgconf cinnamon-desktop
```

Create and activate virtual environment:
```bash
cd ~/.config/fabric
python -m venv venv
source venv/bin/activate
```

Install Fabric:
```bash
pip install --upgrade pip
pip install git+https://github.com/Fabric-Development/fabric.git
pip install psutil
```

## Usage

### Starting the Bar

```bash
cd ~/.config/fabric
./launch.sh
```

Or activate the venv and run directly:
```bash
source ~/.config/fabric/venv/bin/activate
python main.py
```

### Auto-start with Hyprland

Add to your `~/.config/hypr/hyprland.conf`:

```conf
exec-once = ~/.config/fabric/launch.sh
```

### Stopping the Bar

```bash
cd ~/.config/fabric
./stop.sh
```

Or manually:
```bash
pkill -f "python.*main.py"
```

### Restarting the Bar

```bash
cd ~/.config/fabric
./restart.sh
```

## Configuration

### Modifying Special Workspaces

Edit [services/workspace_manager.py](services/workspace_manager.py:30) to change app assignments:

```python
self.apps = {
    "discord": WorkspaceApp("discord", 11, "discord", "discord", "󰙯"),
    "vscode": WorkspaceApp("vscode", 12, "Code", "code", "󰨞"),
    # Add your own apps here
}
```

Parameters:
- `name`: Internal identifier
- `workspace_id`: Workspace number (11+)
- `window_class`: Hyprland window class (use `hyprctl clients`)
- `command`: Launch command
- `icon`: Nerd Font icon

### Customizing Styling

Edit [style.css](style.css) to change colors, fonts, animations, etc.

Key color variables:
```css
:vars {
  --bg-primary: rgba(141, 110, 99, 0.8);
  --accent-pink: rgba(255, 183, 186, 0.6);
  --accent-yellow: rgba(255, 204, 92, 0.8);
  --discord-purple: rgba(179, 157, 219, 1.0);
  --vscode-orange: rgba(255, 138, 101, 1.0);
}
```

### Widget Positions

To change widget popup positions, edit the `anchor` and `margin` parameters in each widget file:

```python
super().__init__(
    layer="overlay",
    anchor="top right",        # Change position
    margin="50px 20px 0px 0px",  # Adjust spacing
    ...
)
```

## Project Structure

```
fabric/.config/fabric/
├── main.py              # Main bar application
├── setup.sh             # Installation script
├── launch.sh            # Startup script
├── style.css            # CSS styling
├── README.md            # This file
├── services/
│   ├── __init__.py
│   └── workspace_manager.py  # Workspace management logic
├── widgets/
│   ├── __init__.py
│   ├── audio.py         # Audio control widget
│   ├── network.py       # Network/Bluetooth widget
│   ├── battery.py       # Battery/power widget
│   ├── power_menu.py    # Power menu widget
│   ├── system_tray.py   # System tray widget
│   └── utility.py       # Utilities widget
└── venv/                # Python virtual environment (created by setup.sh)
```

## Workspace Button Indicators

- **Empty**: Just the icon (app not running)
- **●**: Filled circle (app running in designated workspace)
- **○**: Empty circle (app running in wrong workspace)
- **Bold + Glow**: Active workspace
- **Colored Background**: App-specific colors when active

## Keyboard Shortcuts

Widget windows support keyboard interaction:
- Press `Escape` to close any popup
- Click outside a popup to close it

## Troubleshooting

### Bar doesn't start
1. Check if venv exists: `ls ~/.config/fabric/venv`
2. Verify Fabric installation: `source venv/bin/activate && python -c "import fabric"`
3. Check for errors: Run `python main.py` directly to see error messages

### Workspace buttons not updating
- Ensure Hyprland IPC is working: `hyprctl clients`
- Check window class names match your configuration
- Restart the bar after config changes

### Audio widget shows error / CvcImportError
- Install the missing library: `sudo pacman -S cinnamon-desktop`
- Restart the bar: `pkill -f fabric-bar && ./launch.sh`
- If still not working, ensure PulseAudio/PipeWire is running: `wpctl status`

### Bluetooth not working
- Enable Bluetooth: `sudo systemctl enable --now bluetooth`
- Check bluetoothctl works: `bluetoothctl show`

### Power profiles not working
- Install power-profiles-daemon: `sudo pacman -S power-profiles-daemon`
- Enable it: `sudo systemctl enable --now power-profiles-daemon`

### Styling issues
- CSS errors are logged to console - run `python main.py` directly
- Ensure nerd fonts are installed: `yay -S ttf-jetbrains-mono-nerd ttf-firacode-nerd`

## Migrating from Waybar/AGS

Your old configs remain untouched in:
- `waybar/.config/waybar/`
- `ags/.config/ags/` (deleted per git status)

To test Fabric alongside waybar:
1. Stop waybar: `killall waybar`
2. Start Fabric: `./launch.sh`
3. If issues occur, restart waybar: `waybar &`

To fully switch:
1. Remove waybar from Hyprland autostart
2. Add Fabric to autostart (see Usage section)

## Contributing

This is a personal dotfiles configuration, but feel free to:
- Report issues
- Suggest improvements
- Fork and customize for your setup

## Credits

- **Fabric Framework**: https://github.com/Fabric-Development/fabric
- **Hyprland**: https://hyprland.org
- **Inspiration**: Your previous waybar + ags setup

## License

This configuration is provided as-is for personal use. Fabric framework has its own license.
