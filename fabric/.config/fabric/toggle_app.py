#!/usr/bin/env python3
"""
Standalone script to toggle special workspace apps
Can be called from Hyprland keybindings
"""

import os
import sys
import json
import subprocess

CONFIG_PATH = os.path.expanduser("~/.config/fabric/config.json")

# Fallback if config.json is missing or unreadable
DEFAULT_APPS = {
    "discord": {"workspace": 11, "class": "discord", "command": "discord"},
    "vscode": {"workspace": 12, "class": "Code", "command": "code"},
    "minecraft": {"workspace": 13, "class": "org.prismlauncher.PrismLauncher", "command": "prismlauncher"},
    "steam": {"workspace": 14, "class": "steam", "command": "steam"},
}


def load_apps():
    """Load special workspace apps from the shared fabric config.json"""
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        apps = {
            name: {
                "workspace": app["workspace"],
                "class": app.get("class", name),
                "command": app["command"],
            }
            for name, app in cfg.get("special_workspaces", {}).items()
            if app.get("enabled", True)
        }
        return apps or DEFAULT_APPS
    except Exception:
        return DEFAULT_APPS


def get_windows():
    """Get list of all windows from Hyprland"""
    try:
        output = subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
        return json.loads(output)
    except Exception:
        return []


def get_active_workspace_id():
    """Get the currently active workspace ID"""
    try:
        output = subprocess.check_output(["hyprctl", "activeworkspace", "-j"], text=True)
        data = json.loads(output)
        return data.get("id", 1)
    except Exception:
        return 1


def is_app_running(window_class):
    """Check if app is running anywhere"""
    windows = get_windows()
    for window in windows:
        if window.get("class") == window_class:
            return True
    return False


def is_app_in_workspace(window_class, workspace_id):
    """Check if app is running in specific workspace"""
    windows = get_windows()
    for window in windows:
        if window.get("class") == window_class:
            if window.get("workspace", {}).get("id") == workspace_id:
                return True
    return False


def toggle_app(app_name):
    """Toggle an app - launch or switch to it"""
    apps = load_apps()

    if app_name not in apps:
        print(f"Unknown app: {app_name}")
        print(f"Available apps: {', '.join(apps)}")
        return

    app = apps[app_name]
    workspace_id = app["workspace"]
    window_class = app["class"]
    command = app["command"]

    # Check if app is running
    is_running = is_app_running(window_class)

    if is_running:
        # App is running - move it to designated workspace if not already there
        if not is_app_in_workspace(window_class, workspace_id):
            windows = get_windows()
            for window in windows:
                if window.get("class") == window_class:
                    address = window.get("address", "")
                    if address:
                        subprocess.run(
                            ["hyprctl", "dispatch", "movetoworkspacesilent", f"{workspace_id},address:{address}"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
    else:
        # App is not running - launch it in designated workspace
        subprocess.Popen(
            ["hyprctl", "dispatch", "exec", f"[workspace {workspace_id}] {command}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    # Switch to the designated workspace
    subprocess.run(
        ["hyprctl", "dispatch", "workspace", str(workspace_id)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: toggle_app.py <app_name>")
        print(f"Available apps: {', '.join(load_apps())}")
        sys.exit(1)

    app_name = sys.argv[1]
    toggle_app(app_name)
