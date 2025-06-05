#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import json
import sys

def get_hyprland_clients():
    """Get all Hyprland clients"""
    try:
        result = subprocess.run(['hyprctl', 'clients', '-j'], 
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error getting clients: {e}")
        return []

def get_hyprland_workspaces():
    """Get all Hyprland workspaces"""
    try:
        result = subprocess.run(['hyprctl', 'workspaces', '-j'], 
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error getting workspaces: {e}")
        return []

def get_active_workspace():
    """Get the currently active workspace"""
    try:
        result = subprocess.run(['hyprctl', 'activeworkspace', '-j'], 
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error getting active workspace: {e}")
        return {}

def find_app_window(app_class):
    """Find window by class name"""
    clients = get_hyprland_clients()
    for client in clients:
        if client.get('class', '').lower() == app_class.lower():
            return client
    return None

def is_special_workspace_visible(workspace_name):
    """Check if special workspace is currently visible"""
    active = get_active_workspace()
    return active.get('name') == f'special:{workspace_name}'

def toggle_special_workspace(workspace_name, app_class, app_command):
    """Toggle special workspace for an application"""
    
    # Check if special workspace is currently visible
    if is_special_workspace_visible(workspace_name):
        # Hide the special workspace
        subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', workspace_name], check=True)
        return
    
    # Find the app window
    app_window = find_app_window(app_class)
    
    if app_window:
        # App is running, move it to special workspace if not already there
        current_workspace = app_window.get('workspace', {}).get('name', '')
        if current_workspace != f'special:{workspace_name}':
            subprocess.run([
                'hyprctl', 'dispatch', 'movetoworkspacesilent', 
                f'special:{workspace_name},address:0x{app_window["address"]}'
            ], check=True)
        
        # Show the special workspace
        subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', workspace_name], check=True)
    else:
        # App is not running, launch it in special workspace
        subprocess.run([
            'hyprctl', 'dispatch', 'exec', 
            f'[workspace special:{workspace_name}] {app_command}'
        ], check=True)

def get_workspace_status(workspace_name, app_class):
    """Get the status of a special workspace"""
    
    # Check if visible
    if is_special_workspace_visible(workspace_name):
        return {"text": "", "class": "active"}
    
    # Check if app exists
    app_window = find_app_window(app_class)
    if app_window:
        current_workspace = app_window.get('workspace', {}).get('name', '')
        if current_workspace == f'special:{workspace_name}':
            return {"text": "", "class": "exists"}
        else:
            # App exists but not in special workspace
            return {"text": "", "class": "exists"}
    
    # App doesn't exist
    return {"text": "", "class": "empty"}

def main():
    if len(sys.argv) < 2:
        print("Usage: special-workspace-manager.py <action> [workspace_name]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    # App configurations
    apps = {
        'discord': {
            'class': 'discord',
            'command': 'discord'
        },
        'vscode': {
            'class': 'Code',
            'command': 'code'
        },
        'minecraft': {
            'class': 'Minecraft',
            'command': 'minecraft-launcher'
        }
    }
    
    if action == "toggle" and len(sys.argv) == 3:
        workspace_name = sys.argv[2]
        if workspace_name in apps:
            app = apps[workspace_name]
            toggle_special_workspace(workspace_name, app['class'], app['command'])
        else:
            print(f"Unknown workspace: {workspace_name}")
    
    elif action == "status" and len(sys.argv) == 3:
        workspace_name = sys.argv[2]
        if workspace_name in apps:
            app = apps[workspace_name]
            status = get_workspace_status(workspace_name, app['class'])
            print(json.dumps(status))
        else:
            print(json.dumps({"text": "", "class": "empty"}))
    
    else:
        print("Usage:")
        print("  special-workspace-manager.py toggle <workspace_name>")
        print("  special-workspace-manager.py status <workspace_name>")

if __name__ == "__main__":
    main()
