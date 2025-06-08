# Fastfetch Configuration

A beautiful fastfetch configuration with anime-themed colors matching your waybar and kitty setup, featuring the animated gif from your wallpapers collection.

## Features

- **Anime Room Theme**: Colors inspired by your waybar and kitty configurations
- **Custom Logo**: Uses the `fast-fetch.gif` from your wallpapers directory
- **Nerd Font Icons**: Beautiful icons for all system information
- **Color-coded Information**: Different colors for different types of system info
- **Modular Design**: Easy to customize and extend

## Color Palette

The configuration uses the warm anime room color palette from your existing setup:

- **Primary**: `#ffcc5c` (Golden yellow from kitty cursor)
- **Secondary**: `#b39ddb` (Purple from waybar special workspaces) 
- **Accent**: `#ffb7ba` (Pink from waybar animations)
- **Background**: `#8d6e63` (Brown from waybar modules)
- **Text**: `#f5f0e8` (Light cream from kitty foreground)
- **Highlights**: Various colors matching your kitty ANSI palette

## Files

```
fastfetch/
├── README.md                           # This file
├── .config/
│   └── fastfetch/
│       ├── config.jsonc                # Main configuration
│       └── presets/
│           └── anime-room.jsonc        # Colored preset version
```

## Installation

Using GNU Stow (recommended):

```bash
# Install fastfetch configuration
make fastfetch

# Or manually with stow
stow fastfetch
```

## Usage

```bash
# Use default configuration
fastfetch

# Use the colored anime room preset
fastfetch --config anime-room

# Test the configuration
fastfetch --config ~/.config/fastfetch/config.jsonc
```

## Customization

### Logo Settings

The logo is configured to display your `fast-fetch.gif`:
- **Width**: 35 characters
- **Height**: 20 characters  
- **Type**: kitty (for gif support)
- **Padding**: Optimized spacing

### Color Customization

Edit the color values in `presets/anime-room.jsonc`:
- `keyColor`: Color for the information labels
- `color`: Object with specific color overrides
- `separator`: Color for separator lines

### Module Customization

Add, remove, or modify modules in the `modules` array:
- System information (OS, kernel, uptime)
- Hardware details (CPU, GPU, memory)
- Environment info (DE, WM, theme)
- Network and power status

## Compatibility

- Requires fastfetch installed
- Works best with Kitty terminal for gif display
- Optimized for Nerd Fonts (JetBrainsMono Nerd Font recommended)
- Designed for your Hyprland + Waybar setup

## Integration

This fastfetch configuration is designed to complement:
- Your Kitty terminal with transparency and anime colors
- Your Waybar with matching color scheme
- Your Hyprland window manager setup
- Your overall anime room aesthetic

The colors and styling seamlessly integrate with your existing dotfiles theme.
