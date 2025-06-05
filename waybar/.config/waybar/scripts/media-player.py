#!/home/athoms/.config/waybar/waybar-env/bin/python
import json
import subprocess

def get_media_info():
    try:
        # Get player status
        status = subprocess.check_output(['playerctl', 'status'], text=True).strip()
        artist = subprocess.check_output(['playerctl', 'metadata', 'artist'], text=True, stderr=subprocess.DEVNULL).strip()
        title = subprocess.check_output(['playerctl', 'metadata', 'title'], text=True, stderr=subprocess.DEVNULL).strip()
        
        if status == "Playing":
            icon = ""
        elif status == "Paused":
            icon = ""
        else:
            icon = ""
            
        if artist and title:
            text = f"{artist} - {title}"
            if len(text) > 45:
                text = text[:42] + "..."
        else:
            text = "No media"
            
        return {
            "text": text,
            "icon": icon,
            "class": status.lower(),
            "tooltip": f"Artist: {artist}\nTitle: {title}\nStatus: {status}"
        }
    except subprocess.CalledProcessError:
        return {
            "text": "No player",
            "icon": "",
            "class": "disconnected",
            "tooltip": "No media player running"
        }

if __name__ == "__main__":
    print(json.dumps(get_media_info()))
