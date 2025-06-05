#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import json

def debug_hyprland():
    """Debug Hyprland workspaces and clients"""
    print("=== HYPRLAND DEBUG ===")
    
    try:
        # Check current workspaces
        workspaces_result = subprocess.run(['hyprctl', 'workspaces', '-j'], 
                                         capture_output=True, text=True, check=True)
        workspaces = json.loads(workspaces_result.stdout)
        print(f"Current workspaces: {len(workspaces)}")
        for ws in workspaces:
            print(f"  - {ws.get('name')} (id: {ws.get('id')}, windows: {ws.get('windows', 0)})")
        
        # Check clients
        clients_result = subprocess.run(['hyprctl', 'clients', '-j'], 
                                      capture_output=True, text=True, check=True)
        clients = json.loads(clients_result.stdout)
        print(f"\nCurrent clients: {len(clients)}")
        for client in clients:
            ws_name = client.get('workspace', {}).get('name', 'unknown')
            print(f"  - {client.get('class', 'unknown')} on {ws_name}")
        
        # Check active window
        active_result = subprocess.run(['hyprctl', 'activewindow', '-j'], 
                                     capture_output=True, text=True, check=True)
        if active_result.stdout.strip():
            active = json.loads(active_result.stdout)
            print(f"\nActive window: {active.get('class', 'unknown')} on {active.get('workspace', {}).get('name', 'unknown')}")
        
        # Test special workspace commands
        print("\n=== TESTING SPECIAL WORKSPACE COMMANDS ===")
        test_commands = [
            ['hyprctl', 'dispatch', 'workspace', 'special:discord'],
            ['hyprctl', 'dispatch', 'togglespecialworkspace', 'discord']
        ]
        
        for cmd in test_commands:
            print(f"Testing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"  Return code: {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_hyprland()
