# Complete Waybar Configuration for Hyprland

A comprehensive, modular Waybar setup with Python integration, special workspace management, and custom theming using the Judge Gray, Whiskey, Glacier, and Wedgewood color palette.

## Features

### 🎨 **Cohesive Color Theming**
- **Judge Gray** (#4d3e2a) - Primary background
- **Whiskey** (#d7a46a) - Accent highlights  
- **Glacier** (#7bb4c8) - Text and secondary elements
- **Wedgewood** (#5084ae) - Borders and active states

### 🖥️ **Special Workspace Management**
- **Discord**: `Super + D` - Toggle special workspace
- **VSCode**: `Super + Shift + C` - Toggle special workspace  
- **Minecraft**: `Super + M` - Toggle special workspace
- **Firefox**: `Super + B` - Normal launch (not special workspace)

### 🎵 **Media Integration**
- Real-time media player display with artist/title
- Media controls (play/pause/next/previous)
- Integration with playerctl for all media players

### 🔊 **System Monitoring**
- Volume control with visual feedback and scroll wheel support
- Battery status with charging animations
- WiFi/Bluetooth status with device counts
- System tray integration

### 🇫🇷 **French Localization**
- French calendar display with proper locale handling
- Paris timezone configuration

### 📱 **Notification Center**
- SwayNotificationCenter integration with custom theming
- Do Not Disturb functionality
- Persistent notification history

## Directory Structure

```
~/.dotfiles/
├── waybar/
│   └── .config/
│       └── waybar/
│           ├── config.jsonc           # Main configuration
│           ├── style.css              # Themed styling
│           ├── modules/               # Modular configurations
│           │   ├── workspaces.jsonc   # Workspace management
│           │   ├── media.jsonc        # Media controls
│           │   ├── system.jsonc       # System widgets
│           │   └── custom.jsonc       # Custom widgets
│           └── scripts/               # Python scripts
│               ├── special-workspace.py
│               ├── launch-or-focus.py
│               ├── media-player.py
│               ├── volume-control.py
│               ├── wifi-bluetooth.py
│               └── calendar-french.py
├── hyprland/
│   └── .config/
│       └── hypr/
│           ├── hyprland.conf
│           └── conf/
│               ├── programs.conf      # Updated with waybar/swaync
│               ├── keybindings.conf   # Updated special workspace binds
│               └── rules.conf         # Added workspace rules
├── swaync/
│   └── .config/
│       └── swaync/
│           ├── config.json
│           └── style.css
├── Makefile                           # Easy management
└── README.md
```

## Prerequisites

### Required Packages
```bash
# Core packages
sudo pacman -S waybar swaync playerctl pavucontrol
sudo pacman -S python python-pip
sudo pacman -S stow git

# Optional but recommended
sudo pacman -S nm-connection-editor blueman-manager gnome-calendar
```

### Python Environment Setup
```bash
# Install pyenv (if not already installed)
curl https://pyenv.run | bash

# Install Python 3.11
pyenv install 3.11.7
pyenv global 3.11.7

# Create virtual environment for waybar scripts
cd ~/.config/waybar
python -m venv waybar-env
source waybar-env/bin/activate

# Install required packages
pip install psutil python-dbus-next requests
```

## Installation

### Using GNU Stow (Recommended)
```bash
# Install all configurations (done)
make install

# The configurations are now installed, but waybar needs Hyprland/Wayland to run
# You need to restart Hyprland to activate the new configuration
```

**Important:** Waybar can only run under Wayland/Hyprland, not in X11 or regular terminals.

## Activation

The configuration has been successfully installed! To activate:

1. **Restart Hyprland** to load the new configuration:
   ```bash
   # Log out and log back into Hyprland, or reload config
   hyprctl reload
   ```

2. **The new setup will automatically start:**
   - Waybar will replace hyprpanel
   - SwayNotificationCenter will provide notifications
   - Special workspace keybindings will be active

3. **Test the features:**
   - `Super + D` to test Discord workspace
   - `Super + Shift + C` to test VSCode workspace  
   - `Super + M` to test Minecraft workspace
   - Media controls should work with any playing media
   - Volume control via scroll wheel on volume widget

### Manual Installation
```bash
# Copy configurations manually
cp -r waybar/.config/waybar ~/.config/
cp -r swaync/.config/swaync ~/.config/
cp -r hyprland/.config/hypr ~/.config/

# Make scripts executable
chmod +x ~/.config/waybar/scripts/*.py
```

## Key Bindings

### Special Workspaces
- `Super + D` - Toggle Discord special workspace
- `Super + Shift + C` - Toggle VSCode special workspace
- `Super + M` - Toggle Minecraft special workspace
- `Super + B` - Launch Firefox normally

### System
- `Super + Shift + M` - Exit Hyprland (changed from Super + M)
- `Super + C` - Close active window
- `Super + Q` - Open terminal
- `Super + R` - Open application launcher

### Media Controls (Function Keys)
- `XF86AudioPlay/Pause` - Play/pause media
- `XF86AudioNext/Prev` - Next/previous track
- `XF86AudioRaiseVolume/LowerVolume` - Volume control
- `XF86AudioMute` - Toggle mute

## Widget Interactions

### Special Workspace Indicators
- **Empty**: No indicator shown
- **Exists**: `○` (open circle) - App running but not focused
- **Active**: `●` (filled circle) - App running and focused
- **Click**: Launch app or toggle workspace visibility

### Media Player
- **Left Click**: Play/pause
- **Right Click**: Next track
- **Middle Click**: Previous track
- **Hover**: Shows full song info

### Volume Control
- **Left Click**: Open pavucontrol
- **Right Click**: Toggle mute
- **Scroll Up/Down**: Adjust volume ±2%

### Network Status
- **Left Click**: Open network manager
- **Right Click**: Open Bluetooth manager
- **Icons**: WiFi and Bluetooth status with connection info

### Notification Center
- **Left Click**: Toggle notification panel
- **Right Click**: Toggle Do Not Disturb

## Python Scripts

### special-workspace.py
Monitors workspace status and returns JSON for waybar display:
- Tracks if special workspaces exist and are active
- Returns appropriate CSS classes for styling

### launch-or-focus.py
Smart app launcher that:
- Finds existing app windows
- Moves them to special workspaces
- Launches apps if not running
- Focuses special workspaces

### media-player.py
Media information display:
- Integrates with playerctl
- Shows artist, title, and playback status
- Handles multiple media players

### volume-control.py
Audio system integration:
- Uses wpctl for PipeWire/PulseAudio
- Shows volume percentage and mute status
- Dynamic icon based on volume level

### wifi-bluetooth.py
Network status monitoring:
- WiFi connection status and name
- Bluetooth power and connected device count
- Combined status display

### calendar-french.py
French localized time/date:
- Shows current time in HH:MM:SS format
- Tooltip with full French date
- Handles locale fallbacks gracefully

## Troubleshooting

### Scripts Not Working
```bash
# Check script permissions
ls -la ~/.config/waybar/scripts/

# Make executable if needed
chmod +x ~/.config/waybar/scripts/*.py

# Test individual scripts
~/.config/waybar/scripts/media-player.py
```

### Python Environment Issues
```bash
# Check Python path in scripts
which python3

# Verify virtual environment (if using)
source ~/.config/waybar/waybar-env/bin/activate
pip list
```

### Waybar Not Starting
```bash
# Check configuration syntax
waybar --config ~/.config/waybar/config.jsonc --style ~/.config/waybar/style.css

# Check logs
journalctl --user -f -u waybar
```

### Special Workspaces Not Working
```bash
# Check Hyprland configuration
hyprctl workspaces
hyprctl clients

# Verify window rules
hyprctl windowrules
```

## Customization

### Adding New Special Workspaces
1. Add workspace definition to `hyprland/.config/hypr/conf/rules.conf`
2. Add window rule for the application
3. Add keybinding to `hyprland/.config/hypr/conf/keybindings.conf`
4. Update `waybar/.config/waybar/modules/custom.jsonc`
5. Add app info to Python scripts

### Modifying Colors
Edit the CSS variables in `waybar/.config/waybar/style.css`:
```css
* {
    --judge-gray: #4d3e2a;
    --whiskey: #d7a46a;
    --glacier: #7bb4c8;
    --wedgewood: #5084ae;
}
```

### Adding New Widgets
1. Create widget configuration in appropriate module file
2. Add to main config.jsonc modules list
3. Add styling to style.css
4. Create Python script if needed

## Updates and Maintenance

### Updating Configuration
```bash
cd ~/.dotfiles
git pull
make install
```

### Restarting Services
```bash
# Restart waybar
make restart-waybar

# Restart swaync
pkill swaync && swaync &

# Reload Hyprland config
hyprctl reload
```

## License

This configuration is provided as-is under the MIT License. Feel free to modify and distribute according to your needs.
