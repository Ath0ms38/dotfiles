# Hyprland Configuration - Modular Setup

This Hyprland configuration has been split into multiple files for better organization and maintainability.

## Structure

```
hyprland/
├── .config/
│   └── hypr/
│       ├── hyprland.conf      # Main config file (imports only)
│       ├── hyprpaper.conf     # Wallpaper configuration for hyprpaper
│       └── conf/              # Modular configuration files
│           ├── monitors.conf      # Monitor configuration
│           ├── programs.conf      # Program definitions and autostart
│           ├── environment.conf   # Environment variables and permissions
│           ├── appearance.conf    # General, decoration, and animations
│           ├── input.conf         # Input settings and gestures
│           ├── keybindings.conf   # All keyboard and mouse bindings
│           └── rules.conf         # Window and workspace rules
└── README.md
```

## Configuration Files

### `hyprland.conf`
The main configuration file that imports all modular files using `source` statements.

### `hyprpaper.conf`
- Wallpaper configuration for hyprpaper daemon
- Preloads wallpapers and sets default wallpaper
- IPC settings for dynamic wallpaper changes
- Splash screen configuration

### `conf/monitors.conf`
- Monitor settings and display configuration
- Screen resolution, refresh rate, and positioning

### `conf/programs.conf`
- Program variable definitions (`$terminal`, `$fileManager`, `$menu`)
- Autostart applications and services
- System settings initialization

### `conf/environment.conf`
- Environment variables (cursor size, graphics drivers, etc.)
- Permission settings (commented out by default)

### `conf/appearance.conf`
- General settings (gaps, borders, layout)
- Decoration settings (rounding, shadows, blur)
- Animation configurations and bezier curves
- Layout settings (dwindle, master)
- Misc settings (wallpaper, fonts)

### `conf/input.conf`
- Keyboard layout and settings
- Mouse and touchpad configuration
- Gesture settings
- Per-device input configurations

### `conf/keybindings.conf`
- All keyboard shortcuts and bindings
- Mouse bindings for window management
- Media keys and system controls
- Workspace navigation and window movement

### `conf/rules.conf`
- Window rules and behaviors
- Workspace rules
- Application-specific settings

## Benefits

1. **Maintainability**: Each configuration aspect is isolated in its own file
2. **Readability**: Smaller, focused files are easier to navigate and understand
3. **Modularity**: You can easily enable/disable sections by commenting out source lines
4. **Organization**: Logical grouping makes it easier to find and modify specific settings
5. **Backup/Sharing**: You can share or backup specific configuration aspects independently

## Usage with Stow

This configuration is designed to work with GNU Stow for dotfile management. Use:

```bash
stow hyprland
```

This will create symlinks from `~/.config/hypr/` to the files in this dotfiles repository.

## Making Changes

To modify your Hyprland configuration:

1. Edit the appropriate file in the `conf/` directory
2. Reload Hyprland configuration: `hyprctl reload`
3. Or restart Hyprland: `Super + M` (exit) and restart

## Notes

- All original configuration content has been preserved and organized into logical files
- The configuration maintains full compatibility with Hyprland
- Comments and structure from the original configuration are preserved
