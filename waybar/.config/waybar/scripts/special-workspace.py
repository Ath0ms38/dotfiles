#!/home/athoms/.config/waybar/waybar-env/bin/python
import json
import subprocess
import sys

def get_workspace_status(workspace_name):
    try:
        # Get active workspaces
        workspaces = subprocess.check_output(['hyprctl', 'workspaces', '-j'], text=True)
        workspace_data = json.loads(workspaces)
        
        # Check if special workspace exists and is active
        special_name = f"special:{workspace_name}"
        workspace_exists = any(ws['name'] == special_name for ws in workspace_data)
        
        # Get active window info
        active_window = subprocess.check_output(['hyprctl', 'activewindow', '-j'], text=True)
        active_data = json.loads(active_window) if active_window.strip() != '{}' else {}
        
        is_active = active_data.get('workspace', {}).get('name') == special_name
        
        if is_active:
            status = "active"
            text = "●"
        elif workspace_exists:
            status = "exists"
            text = "○"
        else:
            status = "empty"
            text = ""
            
        return {
            "text": text,
            "class": status,
            "tooltip": f"{workspace_name.title()} workspace - {status}"
        }
    except Exception as e:
        return {
            "text": "?",
            "class": "error",
            "tooltip": f"Error: {str(e)}"
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"text": "?", "class": "error"}))
    else:
        workspace = sys.argv[1]
        print(json.dumps(get_workspace_status(workspace)))
