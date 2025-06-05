#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import sys
import json

APP_CLASSES = {
    'discord': 'discord',
    'vscode': 'Code',
    'minecraft': 'PolyMC'
}

def get_workspace_status(app_name):
    """Get status of special workspace"""
    special_workspace = f"special:{app_name}"
    
    try:
        # Get workspaces
        workspaces_result = subprocess.run(['hyprctl', 'workspaces', '-j'], 
                                         capture_output=True, text=True, check=True)
        workspaces = json.loads(workspaces_result.stdout)
        
        # Check if special workspace exists
        workspace_exists = any(ws.get('name') == special_workspace for ws in workspaces)
        
        # Get active window
        active_result = subprocess.run(['hyprctl', 'activewindow', '-j'], 
                                     capture_output=True, text=True, check=True)
        
        is_active = False
        if active_result.stdout.strip():
            active_window = json.loads(active_result.stdout)
            is_active = active_window.get('workspace', {}).get('name') == special_workspace
        
        # Determine class for CSS styling
        if is_active:
            css_class = "active"
        elif workspace_exists:
            css_class = "exists"
        else:
            css_class = "empty"
        
        return css_class
        
    except Exception as e:
        return "error"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("")
        sys.exit(0)
    
    app_name = sys.argv[1]
    status = get_workspace_status(app_name)
    print(status)
