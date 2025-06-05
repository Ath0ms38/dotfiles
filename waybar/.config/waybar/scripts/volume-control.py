#!/home/athoms/.config/waybar/waybar-env/bin/python
import json
import subprocess
import re

def get_volume_info():
    try:
        # Get volume info using wpctl
        output = subprocess.check_output(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], text=True).strip()
        
        # Parse the output (e.g., "Volume: 0.65" or "Volume: 0.65 [MUTED]")
        volume_match = re.search(r'Volume: ([\d.]+)', output)
        is_muted = '[MUTED]' in output
        
        if volume_match:
            volume = float(volume_match.group(1))
            volume_percent = int(volume * 100)
        else:
            volume_percent = 0
        
        # Choose appropriate icon
        if is_muted:
            icon = "󰖁"
            status_class = "muted"
        elif volume_percent == 0:
            icon = "󰕿"
            status_class = "zero"
        elif volume_percent < 30:
            icon = "󰖀"
            status_class = "low"
        elif volume_percent < 70:
            icon = "󰕾"
            status_class = "medium"
        else:
            icon = "󰕾"
            status_class = "high"
        
        return {
            "text": f"{volume_percent}%",
            "icon": icon,
            "class": status_class,
            "tooltip": f"Volume: {volume_percent}%{' (Muted)' if is_muted else ''}"
        }
        
    except subprocess.CalledProcessError:
        return {
            "text": "N/A",
            "icon": "󰖁",
            "class": "error",
            "tooltip": "Volume control error"
        }

if __name__ == "__main__":
    print(json.dumps(get_volume_info()))
