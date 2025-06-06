#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import json
import sys
import time

def get_workspace_status(workspace_name):
    """Get status of app workspace"""
    try:
        # Get all clients
        clients_result = subprocess.run(['hyprctl', 'clients', '-j'], 
                                      capture_output=True, text=True, check=True)
        clients = json.loads(clients_result.stdout)
        
        # Get active workspace
        active_result = subprocess.run(['hyprctl', 'activeworkspace', '-j'], 
                                     capture_output=True, text=True, check=True)
        active_workspace = json.loads(active_result.stdout)
        
        # App configurations mapped to workspace numbers
        apps = {
            'discord': {'class': 'discord', 'command': 'discord', 'workspace': 11},
            'vscode': {'class': 'Code', 'command': 'code', 'workspace': 12},
            'minecraft': {'class': 'org.polymc.PolyMC', 'command': 'polymc', 'workspace': 13}
        }
        
        if workspace_name not in apps:
            return {"text": "", "class": "", "tooltip": f"Unknown workspace: {workspace_name}"}
        
        app = apps[workspace_name]
        
        # Check if app is running in its workspace
        app_in_workspace = False
        app_running_elsewhere = False
        
        for client in clients:
            client_class = client.get('class', '').lower()
            if client_class == app['class'].lower():
                ws_id = client.get('workspace', {}).get('id', 0)
                if ws_id == app['workspace']:
                    app_in_workspace = True
                else:
                    app_running_elsewhere = True
        
        # Check if this is the active workspace
        is_active = active_workspace.get('id') == app['workspace']
        
        # Determine status
        if app_in_workspace:
            if is_active:
                return {
                    "text": "●",
                    "class": "active",
                    "tooltip": f"{app['class']} is active"
                }
            else:
                return {
                    "text": "●",
                    "class": "exists", 
                    "tooltip": f"{app['class']} is running in workspace {app['workspace']}"
                }
        elif app_running_elsewhere:
            return {
                "text": "○",
                "class": "exists",
                "tooltip": f"{app['class']} is running (not in workspace {app['workspace']})"
            }
        else:
            return {
                "text": "",
                "class": "",
                "tooltip": f"Click to launch {app['class']} in workspace {app['workspace']}"
            }
            
    except Exception as e:
        return {"text": "", "class": "error", "tooltip": f"Error: {e}"}

def manage_workspace(workspace_name):
    """Manage app workspace - launch app or switch to workspace"""
    try:
        # Get current workspace first
        active_result = subprocess.run(['hyprctl', 'activeworkspace', '-j'], 
                                     capture_output=True, text=True, check=True)
        active_workspace = json.loads(active_result.stdout)
        current_workspace = active_workspace.get('id')
        
        # App configurations
        apps = {
            'discord': {'class': 'discord', 'command': 'discord', 'workspace': 11},
            'vscode': {'class': 'Code', 'command': 'code', 'workspace': 12},
            'minecraft': {'class': 'org.polymc.PolyMC', 'command': 'polymc', 'workspace': 13}
        }
        
        if workspace_name not in apps:
            print(f"Unknown workspace: {workspace_name}")
            return
        
        app = apps[workspace_name]
        target_workspace = app['workspace']
        
        # If we're already on the target workspace, just ensure the app is running
        if current_workspace == target_workspace:
            # Get current clients
            clients_result = subprocess.run(['hyprctl', 'clients', '-j'], 
                                          capture_output=True, text=True, check=True)
            clients = json.loads(clients_result.stdout)
            
            # Check if app is running in this workspace
            app_in_workspace = any(
                client.get('class', '').lower() == app['class'].lower() and 
                client.get('workspace', {}).get('id') == target_workspace
                for client in clients
            )
            
            if not app_in_workspace:
                print(f"Launching {app['class']} in workspace {target_workspace}")
                subprocess.run(['hyprctl', 'dispatch', 'exec', app['command']], check=True)
            else:
                print(f"Already on workspace {target_workspace} with {app['class']}")
            return
        
        # Get current clients to check app status
        clients_result = subprocess.run(['hyprctl', 'clients', '-j'], 
                                      capture_output=True, text=True, check=True)
        clients = json.loads(clients_result.stdout)
        
        # Check if app is running anywhere
        app_running = False
        app_in_correct_workspace = False
        
        for client in clients:
            client_class = client.get('class', '').lower()
            if client_class == app['class'].lower():
                app_running = True
                ws_id = client.get('workspace', {}).get('id', 0)
                if ws_id == target_workspace:
                    app_in_correct_workspace = True
                    break
        
        if not app_running:
            # Launch app in its dedicated workspace
            print(f"Launching {app['class']} in workspace {target_workspace}")
            subprocess.run([
                'hyprctl', 'dispatch', 'exec', 
                f'[workspace {target_workspace}] {app["command"]}'
            ], check=True)
            
            # Wait a moment for the app to start, then switch
            time.sleep(0.8)
            subprocess.run([
                'hyprctl', 'dispatch', 'workspace', str(target_workspace)
            ], check=True)
            
        elif not app_in_correct_workspace:
            # Move existing app to its dedicated workspace
            print(f"Moving {app['class']} to workspace {target_workspace}")
            subprocess.run([
                'hyprctl', 'dispatch', 'movetoworkspacesilent', 
                f"{target_workspace},class:{app['class']}"
            ], check=True)
            
            # Switch to the workspace
            subprocess.run([
                'hyprctl', 'dispatch', 'workspace', str(target_workspace)
            ], check=True)
        else:
            # App is already in correct workspace, just switch to it
            print(f"Switching to workspace {target_workspace}")
            subprocess.run([
                'hyprctl', 'dispatch', 'workspace', str(target_workspace)
            ], check=True)
            
    except Exception as e:
        print(f"Error managing workspace: {e}")

def update_waybar_buttons():
    """Trigger waybar button updates after workspace changes"""
    try:
        subprocess.run(['pkill', '-RTMIN+8', 'waybar'], check=False)  # Discord
        subprocess.run(['pkill', '-RTMIN+9', 'waybar'], check=False)  # VSCode
        subprocess.run(['pkill', '-RTMIN+10', 'waybar'], check=False) # Minecraft
    except Exception as e:
        print(f"Error updating waybar: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: regular-workspace-manager.py <action> [workspace_name]")
        print("Actions: status, toggle")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "status":
        if len(sys.argv) != 3:
            print("Usage: regular-workspace-manager.py status <workspace_name>")
            sys.exit(1)
        workspace_name = sys.argv[2]
        result = get_workspace_status(workspace_name)
        print(json.dumps(result))
    
    elif action == "toggle":
        if len(sys.argv) != 3:
            print("Usage: regular-workspace-manager.py toggle <workspace_name>")
            sys.exit(1)
        workspace_name = sys.argv[2]
        manage_workspace(workspace_name)
        # Update waybar buttons after workspace change
        update_waybar_buttons()
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
