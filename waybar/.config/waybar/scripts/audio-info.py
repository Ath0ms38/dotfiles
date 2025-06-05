#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import json
import re

def get_audio_info():
    """Get current audio information"""
    try:
        # Get volume info using wpctl
        result = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], 
                              capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        
        # Parse the output (e.g., "Volume: 0.65" or "Volume: 0.65 [MUTED]")
        volume_match = re.search(r'Volume: ([\d.]+)', output)
        is_muted = '[MUTED]' in output
        
        if volume_match:
            volume = float(volume_match.group(1))
            volume_percent = int(volume * 100)
        else:
            volume_percent = 0
        
        # Determine icon class based on volume level
        if is_muted:
            icon_class = "muted"
            css_class = "muted"
        elif volume_percent == 0:
            icon_class = "low"
            css_class = "zero"
        elif volume_percent < 30:
            icon_class = "low"
            css_class = "low"
        elif volume_percent < 70:
            icon_class = "medium"
            css_class = "medium"
        else:
            icon_class = "high"
            css_class = "high"
        
        tooltip_text = f"🔊 Volume: {volume_percent}%"
        if is_muted:
            tooltip_text += " (Muted)"
        
        return json.dumps({
            "text": f"{volume_percent}%",
            "class": css_class,
            "tooltip": tooltip_text,
            "percentage": volume_percent
        })
        
    except Exception as e:
        return json.dumps({
            "text": "N/A",
            "class": "error",
            "tooltip": f"Audio error: {str(e)}"
        })

if __name__ == "__main__":
    print(get_audio_info())
