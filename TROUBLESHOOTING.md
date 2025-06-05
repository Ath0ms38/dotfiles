# Waybar Troubleshooting Guide

## Issue: Waybar not starting after hyprctl reload

### Quick Fix

1. **Open a native Hyprland terminal** (not VS Code terminal):
   ```bash
   Super + Q  # This opens kitty terminal
   ```

2. **Start waybar manually to see any errors**:
   ```bash
   waybar &
   ```

3. **If waybar shows errors, check logs**:
   ```bash
   waybar 2>&1 | head -20
   ```

### Possible Issues and Solutions

#### 1. Python Scripts Not Found
If you see "required file not found" errors:
```bash
# Check script permissions
ls -la ~/.config/waybar/scripts/
# If not executable:
chmod +x ~/.config/waybar/scripts/*.py
```

#### 2. Python Virtual Environment Issues
If scripts fail to execute:
```bash
# Test scripts manually
cd ~/.config/waybar
python scripts/special-workspace.py discord
```

#### 3. Configuration Syntax Errors
If waybar fails to parse config:
```bash
# Test with minimal config
waybar --config /dev/null --style /dev/null
```

#### 4. Force Restart Waybar
```bash
# Kill any existing waybar instances
pkill waybar
# Start fresh
waybar &
```

### Manual Start Process

If automatic startup isn't working:

1. **Open Hyprland terminal** (`Super + Q`)
2. **Kill existing processes**:
   ```bash
   pkill waybar
   pkill swaync
   ```
3. **Start services manually**:
   ```bash
   waybar &
   swaync &
   ```

### Check What's Running

```bash
# See if waybar is running
ps aux | grep waybar
# See if swaync is running  
ps aux | grep swaync
```

### Alternative: Restart Hyprland Session

If all else fails:
1. Log out of Hyprland
2. Log back in
3. Services should auto-start with the new configuration

### Test Individual Components

```bash
# Test special workspace script
~/.config/waybar/scripts/special-workspace.py discord

# Test media player script
~/.config/waybar/scripts/media-player.py

# Test volume control
~/.config/waybar/scripts/volume-control.py
