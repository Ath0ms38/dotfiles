# Waybar Configuration - Advanced Hyprland Bar

This is a comprehensive Waybar configuration designed for Hyprland with advanced workspace management, modular design, custom Python scripts, and interactive UI elements.

## Structure

```
waybar/
├── .config/
│   ├── fabric/                    # Fabric-based popup scripts
│   │   ├── system_popup.py       # System information popup
│   │   └── volume_popup.py       # Volume control popup
│   └── waybar/
│       ├── config.jsonc          # Main waybar configuration
│       ├── style.css             # Waybar styling and themes
│       ├── modules/              # Modular configuration files
│       │   ├── custom.jsonc      # Custom module definitions
│       │   ├── media.jsonc       # Media player modules
│       │   ├── system.jsonc      # System information modules
│       │   └── workspaces.jsonc  # Workspace-related modules
│       ├── scripts/              # Python and shell scripts
│       │   ├── audio-info.py     # Audio status and control
│       │   ├── battery-popup.py  # Battery information popup
│       │   ├── calendar-popup.py # Calendar popup widget
│       │   ├── media-info.py     # Media player information
│       │   ├── network-popup.py  # Network information popup
│       │   ├── system-stats.py   # System performance stats
│       │   ├── workspace-auto-launcher.py      # Auto-launch apps on workspace switch
│       │   ├── workspace-navigator.py          # Smart workspace navigation
│       │   ├── regular-workspace-manager.py    # Special workspace management
│       │   └── update-special-workspaces.sh    # Workspace status updates
│       └── waybar-env/           # Python virtual environment
└── README.md
```

## Features

### 🎯 Smart Workspace Management
- **Special Workspaces**: Dedicated workspaces for Discord (11), VS Code (12), and Minecraft (13)
- **Auto-launcher**: Automatically launches applications when switching to special workspaces
- **Workspace Navigator**: Smart navigation between workspaces with SUPER+SHIFT+arrows
- **Visual Indicators**: Dynamic icons showing workspace status and application presence

### 🎵 Media Integration
- **Media Player Control**: Play/pause, next/previous track controls
- **Real-time Info**: Current track and artist display
- **Multiple Players**: Support for various media players via playerctl

### 🔊 Audio Management
- **Volume Control**: Click for popup, scroll for quick adjustment
- **Audio Status**: Real-time audio device and volume information
- **Interactive Popup**: Detailed audio control via Fabric popup

### 🖥️ System Monitoring
- **Performance Stats**: CPU, memory, and disk usage
- **Battery Management**: Smart battery indicator with detailed popup
- **Network Status**: Connection status with detailed information popup

### 🎨 Visual Design
- **Custom Icons**: Nerd Font icons for all elements
- **Responsive Layout**: Adapts to different screen sizes
- **Theme Integration**: Consistent styling with Hyprland theme

## Configuration Files

### `config.jsonc`
Main Waybar configuration with three sections:
- **Left**: Workspaces, special workspace indicators, window title
- **Center**: Media player information
- **Right**: System info, audio, network, battery, clock, notifications

### `style.css`
Comprehensive styling including:
- Bar appearance and positioning
- Module-specific styling
- Icon fonts and colors
- Responsive design elements

### `modules/`
Modular configuration files for better organization:
- `custom.jsonc`: Custom module definitions
- `media.jsonc`: Media player modules  
- `system.jsonc`: System information modules
- `workspaces.jsonc`: Workspace-related modules

## Scripts

### Workspace Management
- **`workspace-auto-launcher.py`**: Auto-launches apps on workspace switch
- **`workspace-navigator.py`**: Enhanced workspace navigation
- **`regular-workspace-manager.py`**: Manages special workspace states
- **`update-special-workspaces.sh`**: Updates workspace status indicators

### System Information
- **`system-stats.py`**: CPU, memory, disk usage monitoring
- **`audio-info.py`**: Audio device and volume information
- **`battery-popup.py`**: Detailed battery information
- **`network-popup.py`**: Network connection details

### Interactive Elements
- **`calendar-popup.py`**: Calendar widget popup
- **`media-info.py`**: Media player status and control
- **Fabric Popups**: Advanced popup interfaces for system controls

## Special Workspace Features

### Auto-Launcher System
The workspace auto-launcher provides intelligent application management:

- **Zero Memory Footprint**: Only runs when needed, no background processes
- **Smart Detection**: Launches apps only if not already running
- **Configurable**: Easy to add new applications and workspaces
- **Silent Operation**: Clean operation without user-visible errors

### Workspace Mappings
- **Workspace 11**: Discord (`discord` command)
- **Workspace 12**: VS Code (`code` command)  
- **Workspace 13**: Minecraft (`polymc` command)

### Visual Indicators
Each special workspace shows:
- **Icon**: Application-specific icon (Discord, VS Code, Minecraft)
- **Status**: Visual indication of application presence
- **Click Actions**: Toggle application or switch to workspace

## Usage with Stow

This configuration is designed to work with GNU Stow for dotfile management:

```bash
stow waybar
```

This creates symlinks from `~/.config/waybar/` to the files in this repository.

## Dependencies

### Required Packages
- `waybar` - The main bar application
- `python3` - For custom scripts
- `playerctl` - Media player control
- `wpctl` (pipewire-pulse) - Audio control
- `swaync` - Notification center
- `fabric` - For popup interfaces

### Python Dependencies
A virtual environment is included with required Python packages:
- Standard library modules for system monitoring
- JSON handling for Waybar integration

## Customization

### Adding New Special Workspaces
1. Edit `workspace-auto-launcher.py` to add new app mappings
2. Update `config.jsonc` to add new custom modules
3. Add corresponding icons and styling in `style.css`

### Modifying Scripts
All scripts are well-documented and modular. Common customizations:
- Change workspace numbers in `workspace-auto-launcher.py`
- Modify refresh intervals in module configurations
- Adjust styling in `style.css`

### Color Themes
The configuration uses CSS variables for easy theme customization:
- Edit color definitions in `style.css`
- Modify icon choices in module configurations

## Integration with Hyprland

This Waybar configuration is specifically designed for Hyprland and includes:
- Hyprland workspace integration
- Window title display
- Special workspace management
- Keybinding integration for workspace navigation

## Troubleshooting

### Scripts Not Working
- Ensure scripts are executable: `chmod +x ~/.config/waybar/scripts/*.py`
- Check Python virtual environment: `source ~/.config/waybar/waybar-env/bin/activate`
- Verify dependencies are installed

### Visual Issues
- Check Nerd Font installation for proper icons
- Verify CSS selectors match your Waybar version
- Check console output: `waybar -l debug`

### Workspace Issues
- Verify Hyprland workspace configuration
- Check app class names: `hyprctl clients`
- Ensure keybindings are properly configured in Hyprland

## Contributing

When making changes:
1. Test thoroughly with different screen sizes
2. Ensure Python scripts handle errors gracefully
3. Update documentation for new features
4. Maintain modular structure for easy maintenance
