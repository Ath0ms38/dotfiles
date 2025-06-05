#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import json

def get_media_info():
    """Get current media player information"""
    try:
        # Get player status
        status_result = subprocess.run(['playerctl', 'status'], 
                                     capture_output=True, text=True)
        if status_result.returncode != 0:
            return json.dumps({
                "text": "",
                "class": "disconnected",
                "tooltip": "No media player"
            })
        
        status = status_result.stdout.strip()
        
        # Get metadata
        try:
            artist = subprocess.run(['playerctl', 'metadata', 'artist'], 
                                  capture_output=True, text=True).stdout.strip()
        except:
            artist = ""
        
        try:
            title = subprocess.run(['playerctl', 'metadata', 'title'], 
                                 capture_output=True, text=True).stdout.strip()
        except:
            title = ""
        
        # Format display text
        if artist and title:
            text = f"{artist} - {title}"
            if len(text) > 35:
                text = text[:32] + "..."
        elif title:
            text = title[:35] + ("..." if len(title) > 35 else "")
        else:
            text = "Unknown Track"
        
        # Determine CSS class
        css_class = status.lower() if status in ["Playing", "Paused", "Stopped"] else "unknown"
        
        return json.dumps({
            "text": text,
            "class": css_class,
            "tooltip": f"♪ {artist}\n♫ {title}\n⏸ {status}"
        })
        
    except Exception as e:
        return json.dumps({
            "text": "",
            "class": "error",
            "tooltip": f"Media error: {str(e)}"
        })

if __name__ == "__main__":
    print(get_media_info())
