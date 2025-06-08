# 🐱 Kitty Terminal Configuration

A beautiful, professional transparent terminal theme with warm colors, smooth animations, and developer-friendly features.

## ✨ Features

### **Modern Transparency**
- **90% background opacity** with 64px blur for perfect readability
- **Dynamic opacity controls** via keyboard shortcuts (75% - 100%)
- **Smooth transitions** for all visual effects
- **Professional glassmorphism** aesthetic

### **Beautiful Design**
- **Warm color palette** with browns, yellows, and soft pastels
- **JetBrainsMono Nerd Font** for perfect icon and text rendering
- **Rounded corners** and subtle shadows
- **Powerline-style tabs** with custom colors

### **Developer Experience**
- **Automatic shell detection** (configured to use zsh)
- **Enhanced window management** with shortcuts
- **Tab management** with current directory preservation
- **Performance optimized** for smooth operation

## 🎨 Color Scheme

The configuration uses a carefully chosen warm, professional palette:

```bash
# Core Colors
Background: #3d2f2a (warm brown)
Foreground: #f5f0e8 (cream white)
Cursor: #ffcc5c (golden yellow)
Selection: #ffb7ba (soft pink)

# ANSI Colors
Black: #2d2a2e / #74705d
Red: #ff6b6b / #ffb7ba
Green: #a8e6cf / #dcedc8
Yellow: #ffd93d / #ffcc5c
Blue: #74b9ff / #a29bfe
Magenta: #b39ddb / #fd79a8
Cyan: #81ecec / #00cec9
White: #f5f0e8 / #ffffff
```

## 📁 Files

- `.config/kitty/kitty.conf` - Main Kitty configuration file

## 🚀 Quick Start

### **Prerequisites**
```bash
# Install Kitty
sudo pacman -S kitty

# Install Nerd Font
sudo pacman -S ttf-jetbrains-mono-nerd
```

### **Installation**
```bash
# Install configuration
make kitty

# Or manually
stow --target=$HOME kitty

# Verify installation
kitty --version
```

### **Set as Default Terminal**
```bash
# Update default terminal application
sudo update-alternatives --install /usr/bin/x-terminal-emulator x-terminal-emulator /usr/bin/kitty 50

# Or set in your desktop environment settings
```

## 🛠️ Configuration Details

### **Core Settings**
```bash
# Shell Configuration
shell zsh                        # Automatically use zsh

# Transparency & Background
background_opacity 0.90          # 90% opacity
background #3d2f2a              # Warm brown background
dynamic_background_opacity yes   # Allow runtime opacity changes
background_blur 64               # 64px blur for depth
```

### **Window Styling**
```bash
# Window Configuration
window_margin_width 8            # External margin
window_padding_width 6 10        # Internal padding (vertical, horizontal)
placement_strategy top-left      # Window placement
remember_window_size yes         # Remember last size
initial_window_width 120c        # Default width (120 columns)
initial_window_height 35c        # Default height (35 rows)

# Borders
draw_minimal_borders yes         # Clean border style
active_border_color #ffcc5c      # Golden yellow for active window
inactive_border_color #8d6e63    # Muted brown for inactive
```

### **Font Configuration**
```bash
# Font Settings
font_family JetBrainsMono Nerd Font Regular
bold_font JetBrainsMono Nerd Font Bold
italic_font JetBrainsMono Nerd Font Italic
bold_italic_font JetBrainsMono Nerd Font Bold Italic
font_size 12.0                   # Base font size
adjust_line_height 110%          # Improved readability
```

### **Tab Bar Styling**
```bash
# Tab Configuration
tab_bar_edge top                 # Tabs at top
tab_bar_style powerline          # Powerline-style tabs
tab_bar_margin_width 2           # Tab spacing
active_tab_foreground #8d6e63    # Active tab text color
active_tab_background #ffcc5c    # Active tab background
active_tab_font_style bold       # Bold active tab text
inactive_tab_foreground #f5f0e8  # Inactive tab text
inactive_tab_background #74705d  # Inactive tab background
```

## ⌨️ Keyboard Shortcuts

### **Transparency Controls**
- **Ctrl+Shift+A → 1**: 100% opacity (fully opaque)
- **Ctrl+Shift+A → 2**: 95% opacity
- **Ctrl+Shift+A → 3**: 90% opacity (default)
- **Ctrl+Shift+A → 4**: 85% opacity
- **Ctrl+Shift+A → 5**: 80% opacity
- **Ctrl+Shift+A → 6**: 75% opacity (most transparent)

### **Window Management**
- **Ctrl+Shift+N**: New window with current working directory
- **Ctrl+Shift+T**: New tab with current working directory
- **Ctrl+Shift+W**: Close current tab
- **Ctrl+Shift+Right**: Next tab
- **Ctrl+Shift+Left**: Previous tab

### **Font Control**
- **Ctrl+Shift+Equal**: Increase font size (+2px)
- **Ctrl+Shift+Minus**: Decrease font size (-2px)
- **Ctrl+Shift+Backspace**: Reset font size to default

## 🎯 Key Features

### **Performance Optimized**
```bash
# Performance Settings
repaint_delay 8                  # Fast screen updates
input_delay 0                    # No input lag
sync_to_monitor no               # Better performance on some systems
```

### **Mouse Integration**
```bash
# Mouse Configuration
mouse_hide_wait 3.0              # Hide cursor after 3 seconds
url_color #74b9ff                # Blue color for URLs
url_style curly                  # Underline style for URLs
open_url_with default            # Use system default for URLs
copy_on_select yes               # Auto-copy selected text
```

### **Terminal Bell**
```bash
# Bell Configuration
enable_audio_bell no             # Disable annoying beep
visual_bell_duration 0.0         # No visual flash
```

## 🎨 Customization

### **Change Transparency**
Edit the opacity value in `kitty.conf`:
```bash
background_opacity 0.85  # 85% opacity (more transparent)
background_opacity 0.95  # 95% opacity (less transparent)
```

### **Modify Colors**
Update color values to match your preference:
```bash
# Change background color
background #2d2a2e      # Darker background

# Change accent color
cursor #74b9ff          # Blue accent instead of yellow
active_tab_background #74b9ff
active_border_color #74b9ff
```

### **Font Adjustments**
```bash
font_size 14.0          # Larger font
adjust_line_height 120% # More line spacing
adjust_column_width 1   # Wider characters
```

### **Window Behavior**
```bash
# Disable transparency
background_opacity 1.0
dynamic_background_opacity no

# Different window placement
placement_strategy center
initial_window_width 100c
initial_window_height 30c
```

## 🔧 Troubleshooting

### **Font Issues**
```bash
# Check available fonts
kitty list-fonts | grep -i jetbrains

# Install missing font
sudo pacman -S ttf-jetbrains-mono-nerd

# Test font rendering
kitty +kitten unicode_input
```

### **Transparency Not Working**
```bash
# Check compositor support
echo $XDG_SESSION_TYPE  # Should show wayland or x11

# For X11, ensure compositor is running
ps aux | grep -i compositor

# For Wayland, check for proper support
echo $WAYLAND_DISPLAY
```

### **Shell Not Starting**
```bash
# Check zsh installation
which zsh

# Verify shell setting
grep "shell zsh" ~/.config/kitty/kitty.conf

# Test manual shell launch
kitty --override shell=/usr/bin/zsh
```

### **Performance Issues**
```bash
# Reduce blur for better performance
background_blur 32  # Lower blur value

# Disable transparency
background_opacity 1.0

# Adjust performance settings
repaint_delay 16    # Slower but more stable
sync_to_monitor yes # May help on some systems
```

## 📊 Performance Tips

### **Better Performance**
```bash
# For slower systems
background_blur 16              # Reduce blur
background_opacity 0.95         # Less transparency
repaint_delay 16                # Slower refresh
```

### **Battery Optimization**
```bash
# Reduce resource usage
sync_to_monitor yes             # Sync with display
mouse_hide_wait 1.0             # Hide cursor faster
```

## 🌟 Advanced Features

### **URL Handling**
- **Automatic URL detection** with custom styling
- **Click to open** URLs in default browser
- **Smart URL highlighting** in blue color

### **Copy/Paste Enhancement**
- **Automatic copy** on text selection
- **Smart paste** with formatting preservation
- **Rectangle selection** support

### **Tab Management**
- **Powerline-style tabs** with custom colors
- **Smart tab titles** based on current directory
- **Tab switching** with keyboard shortcuts

### **Window Features**
- **Minimal borders** for clean appearance
- **Smart window placement** and sizing
- **Multi-window support** with proper focus management

## 💡 Tips & Tricks

### **Workflow Integration**
```bash
# Launch with specific directory
kitty --directory ~/projects

# Launch with custom title
kitty --title "Development Terminal"

# Launch with custom session
kitty --session ~/.config/kitty/sessions/dev.conf
```

### **Quick Commands**
```bash
# Test all colors
kitty +kitten themes

# Show detailed configuration
kitty --debug-config

# Performance monitoring
kitty --debug-rendering
```

### **Sessions**
Create session files for different workflows:
```bash
# ~/.config/kitty/sessions/dev.conf
new_tab Development
cd ~/projects
new_tab Testing
cd ~/projects/tests
```

---

## ✨ Result

You get a **beautiful, professional terminal** that's:
- **Visually stunning** with glassmorphism transparency
- **Highly functional** with smart window management
- **Performance optimized** for daily development work
- **Fully customizable** to match your workflow

Perfect for developers who want a **modern, efficient terminal experience** with beautiful aesthetics! 🚀
