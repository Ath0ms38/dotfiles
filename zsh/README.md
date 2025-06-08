# 🐚 Zsh Configuration

A modern, enhanced Zsh shell configuration with beautiful colors, auto-suggestions, syntax highlighting, and developer-friendly features.

## ✨ Features

### **Enhanced Shell Experience**
- **Auto-suggestions**: Gray text completions as you type
- **Syntax Highlighting**: Real-time command highlighting with colors
- **Intelligent History**: Advanced history management with deduplication
- **Smart Completion**: Case-insensitive completion with menu selection

### **Modern Tools Integration**
- **Enhanced `ls`**: Using `eza` with icons and colors
- **Better `cat`**: Using `bat` with syntax highlighting
- **Fuzzy Finding**: `fzf` integration for quick file/command search
- **Smart `grep`**: Using `ripgrep` for faster searching

### **Developer Tools**
- **Git Integration**: Comprehensive git aliases and status functions
- **Python Support**: Virtual environment detection and management
- **Node.js/NPM**: Enhanced package management aliases
- **Archive Extraction**: Universal extract function for any format

## 🎨 Color Theme

The configuration uses a warm, professional color palette:

```bash
# Color Palette
Background: #3d2f2a (warm brown)
Foreground: #f5f0e8 (cream white)
Accent: #ffcc5c (golden yellow)
Highlights: #ffb7ba (soft pink)
```

### **Coordinated Colors**
- **FZF**: Fuzzy finder colors match terminal theme
- **EZA**: File listing colors coordinated with theme
- **Git**: Status colors for clear repository state
- **Completion**: Menu colors for better visibility

## 📁 Files

- `.zshrc` - Main Zsh configuration file with all enhancements

## 🚀 Quick Start

### **Prerequisites**
```bash
# Core packages
sudo pacman -S zsh starship
sudo pacman -S eza bat ripgrep fd fzf

# Oh My Zsh plugins
sudo pacman -S zsh-autosuggestions zsh-syntax-highlighting
```

### **Installation**
```bash
# Install configuration
make zsh

# Or manually
stow --target=$HOME zsh

# Install Oh My Zsh (if not already installed)
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Install Oh My Zsh plugins
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

# Set as default shell
chsh -s /usr/bin/zsh
```

## 🛠️ Configuration Details

### **Oh My Zsh Plugins**
- `git` - Git aliases and completions
- `sudo` - Double ESC to add sudo to command
- `zsh-autosuggestions` - Auto-complete suggestions
- `zsh-syntax-highlighting` - Command syntax highlighting
- `colored-man-pages` - Colorized man pages
- `command-not-found` - Suggests packages for missing commands
- `python` - Python development tools
- `pip` - Python package manager integration
- `virtualenv` - Virtual environment detection

### **Enhanced Aliases**

#### **File Operations**
```bash
ls='eza --icons --group-directories-first'
ll='eza -l --icons --group-directories-first --time-style=relative'
la='eza -la --icons --group-directories-first --time-style=relative'
tree='eza --tree --icons'
cat='bat'
grep='rg'
find='fd'
```

#### **Git Shortcuts**
```bash
ga='git add'
gc='git commit'
gp='git push'
gl='git log --oneline'
gd='git diff'
```

#### **Development Tools**
```bash
py='python'
pip='python -m pip'
venv='python -m venv'
activate='source venv/bin/activate'
```

### **Custom Functions**

#### **Directory Management**
```bash
mkcd() {
    mkdir -p "$1" && cd "$1"
    echo "Created and entered: $1"
}
```

#### **Archive Extraction**
```bash
extract filename.tar.gz  # Supports all major formats
```

#### **Utility Functions**
```bash
weather Paris            # Get weather info
quote                   # Get random quote
git_status             # Enhanced git status
```

#### **Enhanced CD**
- Automatically shows directory contents after changing directories
- Displays current path with home directory shortening
- Falls back gracefully if `eza` is not available

## 🎯 Key Features

### **Smart History**
- **10,000 commands** stored in history
- **Duplicate removal** for cleaner history
- **Space-prefixed commands** ignored (for sensitive commands)
- **Search optimization** with `HIST_FIND_NO_DUPS`

### **Intelligent Completion**
- **Case-insensitive** matching (`m:{a-z}={A-Za-z}`)
- **Visual menu** selection with arrow keys
- **Color-coded** completions matching LS_COLORS
- **Context-aware** suggestions

### **Environment Variables**
```bash
EDITOR="nvim"           # Default editor
BROWSER="firefox"       # Default browser
BAT_THEME="ansi"       # Syntax highlighting theme
```

### **FZF Integration**
- **Ctrl+R**: Fuzzy history search
- **Ctrl+T**: Fuzzy file finder
- **Alt+C**: Fuzzy directory navigation
- **Custom colors** matching terminal theme

## 🎨 Customization

### **Modify Colors**
Edit the color variables in `.zshrc`:
```bash
export FZF_DEFAULT_OPTS="--color=bg+:#3d2f2a,bg:#2d2a2e,..."
export EZA_COLORS="da=1;34:gm=1;35:uu=1;36:..."
```

### **Add Custom Aliases**
Add your own aliases to the aliases section:
```bash
# Personal aliases
alias myproject='cd ~/projects/my-awesome-project'
alias serve='python -m http.server 8000'
```

### **Custom Functions**
Add functions at the end of `.zshrc`:
```bash
# Custom function example
myfunction() {
    echo "Hello from custom function!"
}
```

## 🔧 Troubleshooting

### **Plugins Not Loading**
```bash
# Check if Oh My Zsh is installed
ls ~/.oh-my-zsh

# Verify plugin directories
ls ~/.oh-my-zsh/custom/plugins/

# Reload configuration
source ~/.zshrc
```

### **Colors Not Working**
```bash
# Check terminal capability
echo $TERM

# Test color support
curl -s https://gist.githubusercontent.com/HaleTom/89ffe32783f89f403bba96bd7bcd1263/raw/ | bash
```

### **Auto-suggestions Not Appearing**
```bash
# Check if plugin is loaded
echo $plugins | grep autosuggestions

# Test plugin directly
source ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
```

### **Command Not Found Errors**
```bash
# Install missing tools
sudo pacman -S eza bat ripgrep fd fzf

# Check PATH
echo $PATH
```

## 📊 Performance Tips

### **Faster Startup**
- Plugins are conditionally loaded
- Oh My Zsh handles most plugin management
- Minimal external dependencies

### **Resource Usage**
- **Low memory footprint** with efficient plugins
- **Fast command execution** with modern tools
- **Smart caching** for completions

## 🌟 Advanced Features

### **Zsh Options**
```bash
PROMPT_SUBST           # Allow prompt substitution
AUTO_CD               # Change directory without cd command
GLOB_DOTS             # Include hidden files in globbing
```

### **History Options**
```bash
HIST_EXPIRE_DUPS_FIRST    # Remove duplicates first when trimming
HIST_IGNORE_DUPS          # Don't record duplicate commands
HIST_IGNORE_ALL_DUPS      # Remove older duplicates
HIST_IGNORE_SPACE         # Ignore space-prefixed commands
HIST_FIND_NO_DUPS         # Don't show duplicates in search
HIST_SAVE_NO_DUPS         # Don't save duplicates to history file
```

## 💡 Tips & Tricks

### **Quick Navigation**
- Use `..` to go up one directory
- Use `...` to go up two directories (if AUTO_CD is enabled)
- Use `cd -` to go to previous directory

### **History Search**
- `Ctrl+R` for fuzzy history search
- `!!` to repeat last command
- `!$` to use last argument of previous command

### **Completion**
- `Tab` for completion
- `Tab Tab` for menu selection
- Arrow keys to navigate completion menu

### **Custom Prompt**
The configuration uses Starship for the prompt, which provides:
- **Git status** indicators
- **Python virtual environment** display
- **Directory information** with icons
- **Command execution time** for long commands

---

## ✨ Result

You get a **modern, powerful Zsh configuration** that's:
- **Visually beautiful** with coordinated colors
- **Highly functional** with modern tools
- **Developer-friendly** with git and programming language support
- **Performance optimized** for daily use

Perfect for developers and power users who want a **professional, efficient terminal experience**! 🚀
