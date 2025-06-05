#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import sys
import json
import time

APP_COMMANDS = {
    'discord': 'discord',
    'vscode': 'code', 
    'minecraft': 'polymc'
}

APP_CLASSES = {
    'discord': 'discord',
    'vscode': 'Code',
    'minecraft': 'PolyMC'
}

def get_hyprland_clients():
    """Get all Hyprland windows"""
    try:
        result = subprocess.run(['hyprctl', 'clients', '-j'], 
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except:
        return []

def get_active_workspaces():
    """Get all active workspaces"""
    try:
        result = subprocess.run(['hyprctl', 'workspaces', '-j'], 
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except:
        return []

def find_app_window(app_class):
    """Find window for specific app"""
    clients = get_hyprland_clients()
    for window in clients:
        if app_class.lower() in window.get('class', '').lower():
            return window
    return None

def workspace_exists(workspace_name):
    """Check if workspace exists"""
    workspaces = get_active_workspaces()
    return any(ws.get('name') == workspace_name for ws in workspaces)

def is_workspace_visible(workspace_name):
    """Check if workspace is currently visible"""
    try:
        result = subprocess.run(['hyprctl', 'activewindow', '-j'], 
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            active_window = json.loads(result.stdout)
            return active_window.get('workspace', {}).get('name') == workspace_name
    except:
        pass
    return False

def toggle_special_workspace(app_name):
    """Toggle special workspace for app"""
    special_workspace = f"special:{app_name}"
    app_class = APP_CLASSES.get(app_name)
    app_command = APP_COMMANDS.get(app_name)
    
    if not app_class or not app_command:
        print(f"Unknown app: {app_name}")
        return

    # Check if special workspace exists
    if workspace_exists(special_workspace):
        # If workspace is visible, hide it
        if is_workspace_visible(special_workspace):
            subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', app_name])
        else:
            # Show the workspace
            subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', app_name])
    else:
        # Check if app is running somewhere else
        window = find_app_window(app_class)
        if window:
            # Move existing window to special workspace
            window_address = window['address']
            subprocess.run(['hyprctl', 'dispatch', 'movetoworkspace', 
                          f'{special_workspace},address:{window_address}'])
            time.sleep(0.1)
            subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', app_name])
        else:
            # Launch app in special workspace
            launch_cmd = f'[workspace {special_workspace} silent] {app_command}'
            subprocess.run(['hyprctl', 'dispatch', 'exec', launch_cmd])
            time.sleep(1)
            subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', app_name])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: special-workspace-toggle.py <app_name>")
        sys.exit(1)
    
    app_name = sys.argv[1]
    toggle_special_workspace(app_name)
