#!/usr/bin/env python3
"""
Workspace Navigator for Fabric + Hyprland
Navigates between workspaces and auto-launches apps for special workspaces (11-14)
Reuses toggle_app.py for app launching logic to avoid duplication
"""
import subprocess
import json
import sys
import os

# Workspace to app name mapping (matches toggle_app.py)
WORKSPACE_TO_APP = {
    11: "discord",
    12: "vscode",
    13: "minecraft",
    14: "steam",
}

def get_workspaces():
    """Get all existing workspaces"""
    try:
        result = subprocess.run(['hyprctl', 'workspaces', '-j'],
                              capture_output=True, text=True, check=True)
        workspaces = json.loads(result.stdout)
        return sorted([ws['id'] for ws in workspaces if ws['id'] > 0])
    except Exception:
        return []

def get_active_workspace():
    """Get current active workspace"""
    try:
        result = subprocess.run(['hyprctl', 'activeworkspace', '-j'],
                              capture_output=True, text=True, check=True)
        active = json.loads(result.stdout)
        return active['id']
    except Exception:
        return 1

def launch_app_for_workspace(workspace_id):
    """Launch the app for the given workspace using toggle_app.py"""
    if workspace_id not in WORKSPACE_TO_APP:
        return  # Not a special workspace

    app_name = WORKSPACE_TO_APP[workspace_id]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    toggle_script = os.path.join(script_dir, "toggle_app.py")

    # Use toggle_app.py to handle the app launch/switch logic
    try:
        subprocess.Popen(
            [toggle_script, app_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass  # Silently fail if launch fails

def navigate_workspace(direction):
    """Navigate to next/previous workspace including special workspaces"""
    workspaces = get_workspaces()
    if not workspaces:
        return

    current = get_active_workspace()

    # Include normal workspaces 1-10 and special workspaces 11-14 in navigation
    all_workspaces = sorted(list(set(workspaces + [1, 2, 3, 4, 5, 11, 12, 13, 14])))

    try:
        current_index = all_workspaces.index(current)

        if direction == "next":
            next_index = (current_index + 1) % len(all_workspaces)
        elif direction == "prev":
            next_index = (current_index - 1) % len(all_workspaces)
        else:
            return

        target_workspace = all_workspaces[next_index]

        # If navigating to a special workspace, use toggle_app.py to handle it
        # This ensures app is launched and workspace is switched
        if target_workspace in WORKSPACE_TO_APP:
            launch_app_for_workspace(target_workspace)
        else:
            # Normal workspace - just switch to it
            subprocess.run(['hyprctl', 'dispatch', 'workspace', str(target_workspace)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except ValueError:
        # Current workspace not in list, go to first one
        subprocess.run(['hyprctl', 'dispatch', 'workspace', str(all_workspaces[0])],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    direction = sys.argv[1]
    if direction not in ["next", "prev"]:
        sys.exit(1)

    navigate_workspace(direction)
