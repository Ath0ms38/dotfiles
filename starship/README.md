# ⭐ Starship Prompt Configuration

A beautiful, fast, and customizable prompt for any shell with developer-focused features and a professional color scheme.

## ✨ Features

### **Modern Prompt Design**
- **Clean Layout**: Well-organized information without clutter
- **Professional Colors**: Warm color palette matching terminal theme
- **Fast Performance**: Lightning-fast prompt rendering
- **Cross-shell**: Works with Zsh, Bash, Fish, and more

### **Developer Tools Integration**
- **Git Status**: Branch, ahead/behind, modifications, stash indicators
- **Language Detection**: Automatic detection of Python, Node.js, Rust, Go, etc.
- **Virtual Environments**: Python venv/conda environment display
- **Package Versions**: Current language/tool versions
- **Execution Time**: Command duration for long-running commands

### **Smart Information Display**
- **Directory Path**: Repository-aware path truncation
- **Username/Hostname**: Only shown when relevant (SSH, containers)
- **Battery Status**: When running on battery power
- **Memory Usage**: For resource monitoring
- **Time Display**: Current time with custom formatting

## 🎨 Color Scheme

The configuration uses a carefully chosen warm color palette:

```toml
# Color Palette
primary = "#ffcc5c"      # Golden yellow (main accent)
secondary = "#74b9ff"    # Sky blue (secondary info)
success = "#a8e6cf"      # Mint green (success states)
warning = "#ffd93d"      # Bright yellow (warnings)
error = "#ff6b6b"        # Soft red (errors)
muted = "#74705d"        # Brown gray (secondary text)
text = "#f5f0e8"         # Cream white (primary text)
```

## 📁 Files

- `.config/starship.toml` - Main Starship configuration file

## 🚀 Quick Start

### **Prerequisites**
```bash
# Install Starship
sudo pacman -S starship

# Or install from official installer
curl -sS https://starship.rs/install.sh | sh
```

### **Installation**
```bash
# Install configuration
make starship

# Or manually
stow --target=$HOME starship

# Verify installation
starship --version
```

### **Shell Integration**
Add to your shell configuration:

#### **Zsh (.zshrc)**
```bash
eval "$(starship init zsh)"
```

#### **Bash (.bashrc)**
```bash
eval "$(starship init bash)"
```

#### **Fish (config.fish)**
```bash
starship init fish | source
```

## 🛠️ Configuration Details

### **Prompt Format**
```toml
format = """
$username$hostname$directory$git_branch$git_status
$python$nodejs$rust$golang$java$php
$cmd_duration$character"""
```

### **Directory Module**
- **Truncation**: Intelligent path shortening
- **Git-aware**: Shows repository root when in git repos
- **Home replacement**: `~` for home directory
- **Read-only indicator**: 🔒 for protected directories

### **Git Integration**
```toml
[git_branch]
format = " [$symbol$branch]($style) "
symbol = " "
style = "bold #74b9ff"

[git_status]
format = '([\[$all_status$ahead_behind\]]($style) )'
style = "bold #ff6b6b"
```

#### **Git Status Indicators**
- `?` - Untracked files
- `!` - Modified files
- `+` - Staged files
- `✓` - Clean working tree
- `↑` - Ahead of remote
- `↓` - Behind remote
- `$` - Stashed changes

### **Language Modules**

#### **Python**
```toml
[python]
format = '[${symbol}${pyenv_prefix}(${version} )(\($virtualenv\) )]($style)'
symbol = " "
style = "bold #a8e6cf"
```

#### **Node.js**
```toml
[nodejs]
format = "[$symbol($version )]($style)"
symbol = " "
style = "bold #74b9ff"
```

#### **Other Languages**
- **Rust**: 🦀 with version detection
- **Go**: 🐹 with module detection
- **Java**: ☕ with version info
- **PHP**: 🐘 with version info
- **Docker**: 🐳 when in containerized environment

### **System Information**
```toml
[cmd_duration]
format = " took [$duration]($style)"
style = "bold #ffd93d"
min_time = 2000  # Show for commands > 2 seconds

[memory_usage]
format = " $symbol [${ram}( | ${swap})]($style) "
threshold = 70
symbol = " "
style = "bold #ff6b6b"
```

## 🎯 Key Features

### **Performance Optimized**
- **Async Rendering**: Non-blocking prompt updates
- **Smart Caching**: Efficient git status checking
- **Minimal Dependencies**: Fast startup times

### **Context Awareness**
- **SSH Detection**: Shows username@hostname when remote
- **Container Detection**: Indicates Docker/Podman environments
- **Privilege Escalation**: Different prompt for root/sudo

### **Customizable Segments**
Each module can be independently:
- **Enabled/Disabled**: Turn modules on or off
- **Styled**: Custom colors and formatting
- **Positioned**: Reorder prompt elements
- **Filtered**: Show only in specific contexts

## 🎨 Customization

### **Change Colors**
Edit the color values in `starship.toml`:
```toml
[git_branch]
style = "bold #your_color_here"
```

### **Add Custom Modules**
```toml
[custom.my_module]
command = "echo 'custom info'"
when = "test -f custom_file"
format = "[$output]($style) "
style = "bold green"
```

### **Modify Format**
Reorder or add/remove modules:
```toml
format = """
$username$hostname$directory
$git_branch$git_status$git_metrics
$python$nodejs$rust$golang
$cmd_duration$jobs$battery$time
$character"""
```

### **Language-Specific Settings**
```toml
[python]
python_binary = ["./venv/bin/python", "python", "python3"]
detect_extensions = ["py"]
detect_files = ["requirements.txt", "pyproject.toml"]
```

## 🔧 Troubleshooting

### **Prompt Not Showing**
```bash
# Check Starship installation
which starship

# Test configuration
starship explain

# Validate config file
starship config
```

### **Git Status Slow**
```bash
# Check repository status
git status

# Clean up repository
git gc --aggressive
git repack -ad
```

### **Colors Not Working**
```bash
# Check terminal color support
echo $COLORTERM

# Test Starship colors
starship print-config
```

### **Font Issues**
```bash
# Install Nerd Fonts
sudo pacman -S ttf-jetbrains-mono-nerd

# Test font rendering
echo -e "\ue0b0 \ue0b1 \ue0b2 \ue0b3"
```

## 📊 Performance Tips

### **Git Optimization**
```toml
[git_status]
ahead = "⇡${count}"
diverged = "⇕⇡${ahead_count}⇣${behind_count}"
behind = "⇣${count}"
```

### **Selective Modules**
Disable unused modules for faster rendering:
```toml
[aws]
disabled = true

[gcloud]
disabled = true
```

### **Timeout Settings**
```toml
[cmd_duration]
min_time = 500  # Lower threshold for faster feedback

[directory]
truncation_length = 3  # Shorter paths
```

## 🌟 Advanced Features

### **Conditional Display**
```toml
[username]
show_always = false
format = "[$user]($style)@"

[hostname]
ssh_only = true
format = "[$hostname]($style) "
```

### **Custom Characters**
```toml
[character]
success_symbol = "[❯](bold #a8e6cf)"
error_symbol = "[❯](bold #ff6b6b)"
```

### **Time Display**
```toml
[time]
disabled = false
format = "🕐 [$time]($style) "
time_format = "%T"
style = "bold #74705d"
```

## 💡 Tips & Tricks

### **Quick Config Testing**
```bash
# Test config without saving
starship print-config | starship init zsh --print-full-init
```

### **Module-Specific Testing**
```bash
# Test specific modules
starship module git_branch
starship module python
```

### **Performance Profiling**
```bash
# Profile prompt rendering
starship timings
```

### **Custom Presets**
```bash
# Use predefined configurations
starship preset nerd-font-symbols -o ~/.config/starship.toml
```

---

## ✨ Result

You get a **beautiful, informative prompt** that's:
- **Fast and responsive** with async rendering
- **Developer-friendly** with language detection
- **Visually consistent** with the terminal color scheme
- **Highly customizable** for personal preferences

Perfect for developers who want a **professional, informative shell prompt** that enhances productivity! 🚀
