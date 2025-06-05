# Workspace Auto-Launcher

## Overview
This lightweight script automatically launches applications when you switch to special workspaces if the app isn't already running. It only runs when called - no continuous background process.

## Monitored Workspaces
- **Workspace 11**: Discord
- **Workspace 12**: VS Code  
- **Workspace 13**: Minecraft (PolyMC)

## How It Works
1. The script is called after workspace switches via the workspace navigator
2. It checks the current workspace and determines if it's a special workspace (11, 12, or 13)
3. If the corresponding app isn't running in that workspace, it launches the app
4. If the app is already running, it does nothing
5. The script exits immediately - no background process

## Integration Points
- **Workspace Navigator**: Automatically called when using SUPER+SHIFT+arrows to navigate workspaces
- **Manual Keybindings**: Still works with existing SUPER+D, SUPER+SHIFT+C, SUPER+M keybindings

## Features
- **Zero Memory Footprint**: No background process, only runs when needed
- **Silent Operation**: No output or logging for clean operation
- **Smart Detection**: Only launches apps if they're not already running in the target workspace
- **Instant Execution**: Lightweight script with minimal startup time
- **Error Handling**: Graceful error handling without user-visible errors

## Customization
To add new apps or modify existing ones, edit the `apps` dictionary in the script:

```python
apps = {
    11: {'class': 'discord', 'command': 'discord'},
    12: {'class': 'Code', 'command': 'code'},
    13: {'class': 'org.polymc.PolyMC', 'command': 'polymc'}
}
```

## Manual Usage
You can run the script manually to launch apps for the current workspace:
```bash
~/.config/waybar/scripts/workspace-auto-launcher.py
```

## Troubleshooting
- **Apps not launching**: Verify the app class names match what Hyprland reports (`hyprctl clients`)
- **Script not executable**: Run `chmod +x ~/.config/waybar/scripts/workspace-auto-launcher.py`
- **Integration issues**: Check that the workspace-navigator.py is calling the auto-launcher
