#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import json
import sys

def fix_special_workspace(workspace_name):
    """Fix special workspace by using proper Hyprland commands"""
    
    # App configurations
    apps = {
        'discord': {
            'class': 'discord',
            'command': 'discord',
            'workspace': 'special:discord'
        },
        'vscode': {
            'class': 'Code',
            'command': 'code',
            'workspace': 'special:vscode'
        },
        'minecraft': {
            'class': 'Minecraft',
            'command': 'minecraft-launcher',
            'workspace': 'special:minecraft'
        }
    }
    
    if workspace_name not in apps:
        print(f"Unknown workspace: {workspace_name}")
        return
    
    app = apps[workspace_name]
    
    try:
        # Check if app is running
        clients_result = subprocess.run(['hyprctl', 'clients', '-j'], 
                                      capture_output=True, text=True, check=True)
        clients = json.loads(clients_result.stdout)
        
        app_running = False
        app_on_special = False
        
        for client in clients:
            if client.get('class', '').lower() == app['class'].lower():
                app_running = True
                workspace_name_client = client.get('workspace', {}).get('name', '')
                if workspace_name_client == app['workspace']:
                    app_on_special = True
                break
        
        if not app_running:
            # Launch app on special workspace
            print(f"Launching {app['class']} on {app['workspace']}")
            subprocess.run([
                'hyprctl', 'dispatch', 'exec', 
                f"[workspace {app['workspace']}] {app['command']}"
            ], check=True)
        else:
            if not app_on_special:
                # Move app to special workspace
                print(f"Moving {app['class']} to {app['workspace']}")
                subprocess.run([
                    'hyprctl', 'dispatch', 'movetoworkspacesilent', 
                    f"{app['workspace']},class:{app['class']}"
                ], check=True)
            
            # Toggle special workspace visibility
            print(f"Toggling {app['workspace']}")
            subprocess.run([
                'hyprctl', 'dispatch', 'togglespecialworkspace', workspace_name
            ], check=True)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: fix-special-workspaces.py <workspace_name>")
        sys.exit(1)
    
    fix_special_workspace(sys.argv[1])
