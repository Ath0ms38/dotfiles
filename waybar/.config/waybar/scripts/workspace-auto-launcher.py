#!/home/athoms/.config/waybar/waybar-env/bin/python
"""
Workspace Auto-Launcher for Hyprland
Checks if an app needs to be launched for the current workspace and launches it if needed.
Only runs when called - no continuous background process.
"""

import subprocess
import json
import sys

def get_active_workspace():
    """Get the currently active workspace ID"""
    try:
        result = subprocess.run(['hyprctl', 'activeworkspace', '-j'], 
                              capture_output=True, text=True, check=True)
        workspace_data = json.loads(result.stdout)
        return workspace_data.get('id')
    except Exception:
        return None

def get_clients():
    """Get list of all clients"""
    try:
        result = subprocess.run(['hyprctl', 'clients', '-j'], 
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception:
        return []

def is_app_running_in_workspace(workspace_id, app_class):
    """Check if the app is running in the specified workspace"""
    clients = get_clients()
    
    for client in clients:
        client_class = client.get('class', '').lower()
        client_workspace = client.get('workspace', {}).get('id', 0)
        
        if (client_class == app_class.lower() and 
            client_workspace == workspace_id):
            return True
    
    return False

def launch_app_for_workspace(workspace_id):
    """Launch the app for the given workspace if it's not already running"""
    # App configurations
    apps = {
        11: {'class': 'discord', 'command': 'discord'},
        12: {'class': 'Code', 'command': 'code'},
        13: {'class': 'org.polymc.PolyMC', 'command': 'polymc'}
    }
    
    if workspace_id not in apps:
        return  # Not a special workspace
    
    app = apps[workspace_id]
    
    # Check if app is already running in this workspace
    if is_app_running_in_workspace(workspace_id, app['class']):
        return  # App already running, nothing to do
    
    # Launch the app in the specific workspace
    try:
        subprocess.run([
            'hyprctl', 'dispatch', 'exec', 
            f'[workspace {workspace_id}] {app["command"]}'
        ], check=True)
    except Exception:
        pass  # Silently fail if launch fails

def main():
    """Main function - check current workspace and launch app if needed"""
    workspace_id = get_active_workspace()
    if workspace_id:
        launch_app_for_workspace(workspace_id)

if __name__ == "__main__":
    main()
