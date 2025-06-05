#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import json
import sys

def get_workspaces():
    """Get all workspaces"""
    try:
        result = subprocess.run(['hyprctl', 'workspaces', '-j'], 
                              capture_output=True, text=True, check=True)
        workspaces = json.loads(result.stdout)
        return sorted([ws['id'] for ws in workspaces if ws['id'] > 0])
    except Exception as e:
        print(f"Error getting workspaces: {e}")
        return []

def get_active_workspace():
    """Get current active workspace"""
    try:
        result = subprocess.run(['hyprctl', 'activeworkspace', '-j'], 
                              capture_output=True, text=True, check=True)
        active = json.loads(result.stdout)
        return active['id']
    except Exception as e:
        print(f"Error getting active workspace: {e}")
        return 1

def navigate_workspace(direction):
    """Navigate to next/previous workspace"""
    workspaces = get_workspaces()
    if not workspaces:
        return
    
    current = get_active_workspace()
    
    # Include our app workspaces in navigation
    all_workspaces = sorted(list(set(workspaces + [1, 2, 3, 4, 5, 11, 12, 13])))
    
    try:
        current_index = all_workspaces.index(current)
        
        if direction == "next":
            next_index = (current_index + 1) % len(all_workspaces)
        elif direction == "prev":
            next_index = (current_index - 1) % len(all_workspaces)
        else:
            print(f"Unknown direction: {direction}")
            return
        
        target_workspace = all_workspaces[next_index]
        
        # Switch to the target workspace
        subprocess.run(['hyprctl', 'dispatch', 'workspace', str(target_workspace)], 
                      check=True)
        
        # Auto-launch app if needed for special workspaces
        subprocess.run(['/home/athoms/dotfiles/waybar/.config/waybar/scripts/workspace-auto-launcher.py'], 
                      capture_output=True)
        
    except ValueError:
        # Current workspace not in list, go to first one
        subprocess.run(['hyprctl', 'dispatch', 'workspace', str(all_workspaces[0])], 
                      check=True)
    except Exception as e:
        print(f"Error navigating workspace: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: workspace-navigator.py <next|prev>")
        sys.exit(1)
    
    direction = sys.argv[1]
    if direction not in ["next", "prev"]:
        print("Direction must be 'next' or 'prev'")
        sys.exit(1)
    
    navigate_workspace(direction)
