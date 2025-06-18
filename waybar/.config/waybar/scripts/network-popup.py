#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import json
import sys

def get_wifi_networks():
    """Get available WiFi networks"""
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,IN-USE', 'device', 'wifi', 'list'], 
                              capture_output=True, text=True)
        networks = []
        for line in result.stdout.strip().split('\n'):
            if line and line.strip():
                parts = line.split(':')
                if len(parts) >= 4:
                    ssid, signal, security, in_use = parts[0], parts[1], parts[2], parts[3]
                    if ssid and ssid != '--':
                        icon = "📶" if in_use == "*" else "📡"
                        sec_icon = "🔒" if security and security != '--' else "🔓"
                        signal_bars = "▂▄▆█"[min(3, int(signal)//25)] if signal.isdigit() else "?"
                        networks.append({
                            'ssid': ssid,
                            'signal': signal,
                            'security': security,
                            'in_use': in_use == "*",
                            'display': f"{icon} {ssid} {signal_bars} {sec_icon}"
                        })
        return networks
    except Exception as e:
        return []

def get_current_connection():
    """Get current connection info"""
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show', '--active'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            connections = []
            for line in lines:
                parts = line.split(':')
                if len(parts) >= 3:
                    connections.append(f"{parts[0]} ({parts[1]}) on {parts[2]}")
            return connections
        return []
    except:
        return []

def create_wifi_manager_script():
    """Create a simple interactive WiFi manager script"""
    script_content = '''#!/bin/bash

# WiFi Manager for Waybar
echo "🔥 Custom WiFi Manager 🔥"
echo "=========================="
echo ""

# Function to show current connection
show_current() {
    echo "📡 Current Connection:"
    nmcli -t -f NAME,TYPE,DEVICE connection show --active | while IFS=':' read name type device; do
        if [ ! -z "$name" ]; then
            echo "  ✓ $name ($type) on $device"
        fi
    done
    echo ""
}

# Function to show available networks
show_networks() {
    echo "📶 Available WiFi Networks:"
    echo "   SSID                     Signal  Security"
    echo "   ----                     ------  --------"
    nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE device wifi list | head -20 | while IFS=':' read ssid signal security inuse; do
        if [ ! -z "$ssid" ] && [ "$ssid" != "--" ]; then
            if [ "$inuse" = "*" ]; then
                status="⚡"
            else
                status="  "
            fi
            
            if [ ! -z "$security" ] && [ "$security" != "--" ]; then
                sec_icon="🔒"
            else
                sec_icon="🔓"
            fi
            
            printf "   %-25s %3s%%   %s %s\\n" "$ssid" "$signal" "$sec_icon" "$status"
        fi
    done
    echo ""
}

# Function to connect to network
connect_wifi() {
    echo "Enter the SSID of the network you want to connect to:"
    read -p "SSID: " ssid
    if [ ! -z "$ssid" ]; then
        echo "Connecting to $ssid..."
        if nmcli device wifi connect "$ssid"; then
            echo "✅ Successfully connected to $ssid"
        else
            echo "❌ Failed to connect to $ssid"
            echo "The network might require a password. Try using nmtui for password-protected networks."
        fi
    fi
}

# Main menu
while true; do
    clear
    echo "🔥 Custom WiFi Manager 🔥"
    echo "=========================="
    echo ""
    
    show_current
    show_networks
    
    echo "Options:"
    echo "  1) Refresh networks"
    echo "  2) Connect to network"
    echo "  3) Open nmtui (full network manager)"
    echo "  4) Disconnect current WiFi"
    echo "  5) Exit"
    echo ""
    
    read -p "Choose an option (1-5): " choice
    
    case $choice in
        1)
            echo "Refreshing..."
            nmcli device wifi rescan 2>/dev/null
            sleep 1
            ;;
        2)
            connect_wifi
            read -p "Press Enter to continue..."
            ;;
        3)
            nmtui
            ;;
        4)
            echo "Disconnecting WiFi..."
            nmcli device disconnect $(nmcli -t -f DEVICE,TYPE device status | grep wifi | cut -d: -f1 | head -1)
            read -p "Press Enter to continue..."
            ;;
        5)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option. Try again."
            sleep 1
            ;;
    esac
done
'''
    
    # Write the script to a temporary file
    import tempfile
    import os
    
    script_file = '/tmp/wifi_manager.sh'
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    # Make it executable
    os.chmod(script_file, 0o755)
    return script_file

def show_wifi_selector():
    """Show the custom WiFi manager"""
    try:
        script_file = create_wifi_manager_script()
        subprocess.run(['kitty', '--title', 'WiFi Manager', '-e', script_file])
    except Exception as e:
        # Fallback to nmtui
        subprocess.run(['kitty', '--title', 'Network Manager', '-e', 'nmtui'])

def handle_selection(selected, networks):
    """Handle the user's selection"""
    if "Open nmtui" in selected:
        subprocess.run(['kitty', '--title', 'Network Manager', '-e', 'nmtui'])
    elif "Refresh networks" in selected:
        show_wifi_selector()
    elif "Cancel" in selected:
        return
    else:
        # Try to connect to selected network
        for net in networks:
            if net['ssid'] in selected and not net['in_use']:
                try:
                    subprocess.run(['nmcli', 'device', 'wifi', 'connect', net['ssid']], check=True)
                    subprocess.run([
                        'notify-send',
                        '✅ WiFi Connected',
                        f"Connected to {net['ssid']}"
                    ])
                except subprocess.CalledProcessError:
                    subprocess.run([
                        'notify-send',
                        '❌ Connection Failed',
                        f"Failed to connect to {net['ssid']}"
                    ])
                break

def show_network_popup():
    """Show network information and open WiFi selector"""
    try:
        current = get_current_connection()
        networks = get_wifi_networks()
        
        # Show current status
        if current:
            status_text = f"Connected: {current[0]}"
        else:
            status_text = "No active connections"
            
        if networks:
            connected_net = next((n for n in networks if n['in_use']), None)
            if connected_net:
                status_text += f"\nWiFi: {connected_net['ssid']} ({connected_net['signal']}%)"
        
        subprocess.run([
            'notify-send',
            '📶 Network Status',
            status_text
        ])
        
        # Open WiFi selector
        show_wifi_selector()
        
    except Exception as e:
        subprocess.run([
            'notify-send',
            '❌ Network Error',
            f"Error: {str(e)}"
        ])

if __name__ == "__main__":
    show_network_popup()
