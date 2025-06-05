#!/home/athoms/.config/waybar/waybar-env/bin/python
import json
import subprocess
import re

def get_wifi_status():
    try:
        # Get WiFi status using nmcli
        output = subprocess.check_output(['nmcli', '-t', '-f', 'WIFI,STATE', 'general'], text=True).strip()
        lines = output.split('\n')
        
        wifi_enabled = False
        wifi_connected = False
        
        for line in lines:
            if line.startswith('WIFI:'):
                wifi_enabled = 'enabled' in line
            elif line.startswith('STATE:'):
                wifi_connected = 'connected' in line
        
        if wifi_connected:
            # Get connection name
            try:
                conn_output = subprocess.check_output(['nmcli', '-t', '-f', 'NAME', 'connection', 'show', '--active'], text=True).strip()
                wifi_name = conn_output.split('\n')[0] if conn_output else "Connected"
            except:
                wifi_name = "Connected"
            return {"connected": True, "name": wifi_name}
        elif wifi_enabled:
            return {"connected": False, "name": "Disconnected"}
        else:
            return {"connected": False, "name": "Disabled"}
    except:
        return {"connected": False, "name": "Error"}

def get_bluetooth_status():
    try:
        # Check if bluetooth is powered on
        output = subprocess.check_output(['bluetoothctl', 'show'], text=True)
        powered_on = 'Powered: yes' in output
        
        if powered_on:
            # Check for connected devices
            try:
                devices_output = subprocess.check_output(['bluetoothctl', 'devices', 'Connected'], text=True)
                connected_devices = len([line for line in devices_output.strip().split('\n') if line.strip()])
                if connected_devices > 0:
                    return {"enabled": True, "connected": connected_devices}
                else:
                    return {"enabled": True, "connected": 0}
            except:
                return {"enabled": True, "connected": 0}
        else:
            return {"enabled": False, "connected": 0}
    except:
        return {"enabled": False, "connected": 0}

def get_network_info():
    wifi = get_wifi_status()
    bluetooth = get_bluetooth_status()
    
    # WiFi icon
    if wifi["connected"]:
        wifi_icon = "󰖩"
        wifi_class = "connected"
    else:
        wifi_icon = "󰖪"
        wifi_class = "disconnected"
    
    # Bluetooth icon
    if bluetooth["enabled"] and bluetooth["connected"] > 0:
        bt_icon = "󰂯"
        bt_class = "connected"
    elif bluetooth["enabled"]:
        bt_icon = "󰂲"
        bt_class = "enabled"
    else:
        bt_icon = "󰂲"
        bt_class = "disabled"
    
    # Combine status
    text = f"{wifi_icon} {bt_icon}"
    
    tooltip_lines = [
        f"WiFi: {wifi['name']}",
        f"Bluetooth: {'On' if bluetooth['enabled'] else 'Off'}"
    ]
    
    if bluetooth["connected"] > 0:
        tooltip_lines.append(f"BT Devices: {bluetooth['connected']}")
    
    return {
        "text": text,
        "class": f"{wifi_class} {bt_class}",
        "tooltip": "\n".join(tooltip_lines)
    }

if __name__ == "__main__":
    print(json.dumps(get_network_info()))
