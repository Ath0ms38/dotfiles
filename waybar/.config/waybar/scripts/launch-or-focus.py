#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import json
import sys
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

def find_app_window(app_class):
    try:
        clients = subprocess.check_output(['hyprctl', 'clients', '-j'], text=True)
        windows = json.loads(clients)
        return next((w for w in windows if app_class.lower() in w['class'].lower()), None)
    except:
        return None

def launch_or_focus_app(app_name):
    special_workspace = f"special:{app_name}"
    app_class = APP_CLASSES.get(app_name)
    app_command = APP_COMMANDS.get(app_name)
    
    if not app_class or not app_command:
        print(f"Unknown app: {app_name}")
        return
    
    # Check if app is already running
    window = find_app_window(app_class)
    
    if window:
        # App exists, move it to special workspace and focus
        window_address = window['address']
        subprocess.run(['hyprctl', 'dispatch', 'movetoworkspace', f'{special_workspace},address:{window_address}'])
        subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', app_name])
    else:
        # App doesn't exist, launch it in special workspace
        launch_cmd = f'[workspace {special_workspace} silent] {app_command}'
        subprocess.run(['hyprctl', 'dispatch', 'exec', launch_cmd])
        time.sleep(1)  # Give app time to start
        subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', app_name])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: launch-or-focus.py <app_name>")
        sys.exit(1)
    
    app_name = sys.argv[1]
    launch_or_focus_app(app_name)
