# ✨ Dotfiles - Hyprland & Waybar Configuration

A comprehensive dotfiles repository featuring a modular Hyprland configuration and advanced Waybar setup with intelligent workspace management, custom scripts, and modern visual effects.

## 🏗️ Project Structure

```
dotfiles/
├── hyprland/           # Modular Hyprland configuration
├── waybar/             # Advanced Waybar with smart features
├── swaync/             # Notification center configuration
├── kitty/              # Beautiful transparent terminal theme
├── starship/           # Modern shell prompt configuration
├── zsh/                # Enhanced zsh shell configuration
├── wallpapers/         # Desktop wallpapers
├── Makefile           # Installation automation
├── README.md          # This file
└── TROUBLESHOOTING.md # Common issues and solutions
```

## 🖥️ Hyprland Configuration

### **Modular Design**
- **Split configuration** into logical files for better maintainability
- **Easy customization** with separate files for each aspect
- **Version control friendly** with smaller, focused files

### **Configuration Files**
- `hyprland.conf` - Main config with imports
- `hyprpaper.conf` - Wallpaper management
- `conf/monitors.conf` - Display settings
- `conf/programs.conf` - Application definitions
- `conf/environment.conf` - Environment variables
- `conf/appearance.conf` - Visual settings and animations
- `conf/input.conf` - Keyboard and mouse settings
- `conf/keybindings.conf` - All keyboard shortcuts
- `conf/rules.conf` - Window and workspace rules

## 🎨 Waybar - Advanced System Bar

### **Smart Workspace Management Features**
- **Special Workspaces**: Dedicated workspaces for Discord (11), VS Code (12), and Minecraft (13)
- **Auto-launcher**: Automatically launches applications when switching to special workspaces
- **Workspace Navigator**: Enhanced navigation with SUPER+SHIFT+arrow keys
- **Visual Indicators**: Dynamic icons showing workspace status and application presence
- **Modular Configuration**: Split into logical modules for easy maintenance

### **Interactive System Monitoring**
- **Audio Control**: Click for popup, scroll for volume adjustment
- **System Stats**: CPU, memory, disk usage with interactive popups
- **Battery Management**: Smart indicator with detailed information popup
- **Network Status**: Connection details with popup interface
- **Media Integration**: Real-time media player control and information

## 💻 Terminal Configuration

### **Beautiful Terminal Experience**
- **Kitty Terminal**: 90% transparency with background blur effects
- **Starship Prompt**: Modern, informative prompt with git integration
- **Zsh Shell**: Enhanced shell with auto-suggestions and syntax highlighting
- **Consistent Color Theme**: Warm color palette matching the desktop aesthetic

### **Enhanced Features**
- **Auto-suggestions**: Gray text completions as you type
- **Syntax Highlighting**: Real-time command highlighting with colors
- **Modern File Listing**: Enhanced `ls` with icons and colors via `eza`
- **Fuzzy Finding**: Quick file/command search with `fzf`
- **Developer Tools**: Git integration, Python support, virtual environment detection

### **Terminal Transparency**
- **Dynamic Opacity**: Adjustable transparency (75% - 100%)
- **Background Blur**: 64px blur for depth and readability
- **Color Coordination**: Terminal colors match the desktop theme
- **Professional Appearance**: Clean, distraction-free interface

## 🎨 Design Features

### **Glassmorphism Aesthetic**
- **Transparent background** with blur effects
- **Rounded corners** and smooth animations
- **Gradient borders** with dynamic glow effects
- **Cyberpunk-inspired color palette**: Dark blues, cyan accents, purple highlights

### **Smart Visual States**
- **Hover effects** with smooth transforms and glows
- **Active state animations** with pulsing effects
- **Battery charging** animations
- **Media playing** pulse indicators
- **System status** color coding (green/yellow/red)

### **Modern Icons**
- **Nerd Font icons** for clean, consistent appearance
- **Context-aware icons** that change based on status
- **Proper spacing** and visual hierarchy

## 🚀 Special Workspace System

### **Intelligent Management**
- **Auto-detection** of running applications
- **Smart launching** - opens app if not running, focuses if running
- **Visual indicators** showing workspace status
- **Seamless toggling** between show/hide states

### **Keybindings**
- `Super + D` → Discord special workspace
- `Super + Shift + C` → VSCode special workspace  
- `Super + M` → Minecraft special workspace
- `Super + B` → Firefox (normal launch)

### **Visual States**
- **Empty**: No indicator (app not running)
- **Exists**: Colored background (app running, workspace hidden)
- **Active**: Glowing animation (workspace visible and focused)

## 📱 Popup Widgets

Instead of opening applications, clicking widgets shows beautiful popup notifications:

### **Audio Control**
- **Volume bar** with visual representation
- **Mute status** indicator
- **Scroll wheel** volume adjustment
- **Click** for popup with detailed info

### **System Information**
- **CPU usage** with color-coded alerts
- **Memory** and **disk usage**
- **Temperature monitoring** (if available)
- **Detailed tooltips** with full stats

### **Battery Status**
- **Charging animations** when plugged in
- **Time remaining** estimates
- **Warning colors** for low battery
- **Click** for detailed battery info popup

### **Network Information**
- **WiFi signal strength** display
- **Connection status** indicators
- **Click** to open network manager
- **Hover** for detailed connection info

### **Calendar**
- **French localization** with proper formatting
- **Click** for date/time popup
- **Week number** display

## 🎵 Media Integration

### **Smart Media Player**
- **Auto-detection** of any playing media
- **Artist and title** display with truncation
- **Playback controls** via clicks
- **Visual playing indicator** with animations

### **Controls**
- **Left Click**: Play/pause
- **Right Click**: Next track  
- **Middle Click**: Previous track
- **Scroll**: Volume control (on audio widget)

## 💫 Advanced Features

### **Performance Optimized**
- **Efficient Python scripts** with minimal resource usage
- **Smart update intervals** (1-5 seconds depending on widget)
- **Error handling** with graceful fallbacks

### **Modular Design**
- **Single configuration file** with all modules
- **Easy customization** via CSS variables
- **Extensible script system**

### **Responsive Layout**
- **Auto-sizing** based on content
- **Consistent spacing** and alignment
- **Screen-aware** positioning

## 📂 Component Documentation

For detailed information about each component:

- **[Hyprland Configuration](hyprland/README.md)** - Complete guide to the modular Hyprland setup
- **[Waybar Configuration](waybar/README.md)** - Advanced Waybar features and customization
- **[Kitty Terminal](kitty/README.md)** - Beautiful transparent terminal configuration
- **[Starship Prompt](starship/README.md)** - Modern shell prompt setup and customization
- **[Zsh Configuration](zsh/README.md)** - Enhanced shell with plugins and themes
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

## 🛠️ Installation

### **Prerequisites**
```bash
# Core packages
sudo pacman -S waybar swaync playerctl pavucontrol
sudo pacman -S python python-pip python-psutil
sudo pacman -S ttf-jetbrains-mono-nerd

# Terminal packages
sudo pacman -S kitty zsh starship
sudo pacman -S eza bat ripgrep fd fzf
sudo pacman -S zsh-autosuggestions zsh-syntax-highlighting

# Optional utilities
sudo pacman -S nm-connection-editor brightnessctl
```

### **Install Configuration**
```bash
# From your dotfiles directory
make install

# Or manual installation
stow --target=$HOME waybar hyprland swaync kitty starship zsh
chmod +x ~/.config/waybar/scripts/*.py
```

### **Terminal Setup**
```bash
# Install Oh My Zsh (if not already installed)
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Install zsh plugins for Oh My Zsh
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

# Set zsh as default shell
chsh -s /usr/bin/zsh
```

### **Activate**
```bash
# Kill existing waybar
pkill waybar

# Start new beautiful waybar
waybar &

# Or restart Hyprland to auto-start
hyprctl reload
```

## 🎨 Customization

### **Color Palette**
The setup uses a carefully chosen cyberpunk-inspired palette:

```css
/* Main colors */
background: rgba(13, 17, 23, 0.85)     /* Dark blue-black */
primary: rgba(139, 233, 253, 0.3)      /* Cyan accent */
secondary: rgba(187, 154, 247, 0.2)    /* Purple highlight */
text: #e6edf3                          /* Light blue-white */
```

### **App-Specific Colors**
- **Discord**: Purple theme (`#5865f2`)
- **VSCode**: Blue theme (`#0078d7`)  
- **Minecraft**: Green theme (`#50c878`)

### **Modify Colors**
Edit `waybar/.config/waybar/style.css` to change:
- **Background opacity**: Change `rgba()` alpha values
- **Accent colors**: Update color values in hover states
- **Animation speeds**: Adjust `transition` durations

### **Add New Special Workspaces**
1. **Update scripts**: Add app info to `special-workspace-*.py`
2. **Add configuration**: Include new widget in `config.jsonc`
3. **Add styling**: Create CSS rules for the new app
4. **Add keybinding**: Update `keybindings.conf`

## 🔧 Troubleshooting

### **Scripts Not Working**
```bash
# Test individual scripts
~/.config/waybar/scripts/special-workspace-status.py discord
~/.config/waybar/scripts/media-info.py

# Check permissions
ls -la ~/.config/waybar/scripts/
```

### **Waybar Won't Start**
```bash
# Test with debug output
waybar --log-level debug

# Check for syntax errors
waybar --config ~/.config/waybar/config.jsonc --style ~/.config/waybar/style.css
```

### **Special Workspaces Issues**
```bash
# Check Hyprland status
hyprctl workspaces
hyprctl clients

# Test manual toggle
~/.config/waybar/scripts/special-workspace-toggle.py discord
```

### **Missing Icons**
```bash
# Install nerd fonts
sudo pacman -S ttf-jetbrains-mono-nerd ttf-nerd-fonts-symbols-mono

# Or download from: https://www.nerdfonts.com/
```

## 📊 Widget Status Reference

### **Special Workspace Classes**
- `.empty` → App not running
- `.exists` → App running, workspace hidden  
- `.active` → Workspace visible and focused

### **System Status Classes**
- `.normal` → All systems good (< 70% usage)
- `.warning` → High usage (70-90%)
- `.critical` → Very high usage (> 90%)

### **Audio Classes**
- `.muted` → Audio muted
- `.low/.medium/.high` → Volume levels

### **Battery Classes**
- `.charging` → Plugged in and charging
- `.warning` → Low battery (< 30%)
- `.critical` → Very low battery (< 15%)

## 🎯 Tips & Tricks

### **Performance**
- **Disable animations** on lower-end systems by setting `transition: none`
- **Increase update intervals** in config for better performance
- **Use simpler backgrounds** if blur effects are slow

### **Customization**
- **Extract colors** from your wallpaper using tools like `imagemagick`
- **Adjust transparency** based on your wallpaper brightness
- **Create themes** by saving different CSS files

### **Workflow**
- **Use special workspaces** for persistent apps (Discord, IDE, etc.)
- **Regular workspaces** for temporary tasks
- **Popup widgets** for quick system checks without opening full apps

## 📱 Modern Features

### **Glassmorphism Effects**
- **Backdrop blur** for depth
- **Subtle borders** with transparency
- **Layered shadows** for dimension

### **Smooth Animations**
- **Cubic-bezier** easing for natural motion
- **Transform animations** for hover effects
- **Opacity transitions** for state changes

### **Smart Interactions**
- **Progressive disclosure** - simple view with detailed popups
- **Context-aware** behaviors based on system state
- **Minimal cognitive load** with clear visual hierarchy

---

## ✨ Result

You now have a **gorgeous, modern waybar** that's:
- **Visually stunning** with glassmorphism effects
- **Highly functional** with intelligent popups
- **Performance optimized** with efficient scripts  
- **Fully customizable** to match your aesthetic

Perfect for anyone who wants a **professional, anime-inspired desktop** that's both beautiful and practical! 🌸✨
