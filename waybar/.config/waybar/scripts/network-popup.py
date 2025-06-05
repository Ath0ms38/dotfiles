#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess

def show_network_popup():
    """Show network information popup"""
    try:
        # Get network info
        wifi_info = subprocess.run(['nmcli', 'device', 'wifi', 'list'], 
                                 capture_output=True, text=True)
        
        # Show notification with basic network info
        subprocess.run([
            'notify-send',
            '-t', '4000',
            '📶 Network Information',
            'Click to open network manager'
        ])
        
        # Optionally open network manager
        subprocess.run(['nm-connection-editor'], check=False)
        
    except Exception as e:
        subprocess.run([
            'notify-send',
            '-t', '3000',
            'Network Error',
            str(e)
        ])

if __name__ == "__main__":
    show_network_popup()
