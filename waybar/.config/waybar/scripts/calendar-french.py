#!/home/athoms/.config/waybar/waybar-env/bin/python
import json
import datetime
import locale

def get_french_date():
    # Set French locale if available
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR')
        except locale.Error:
            # Fallback to C locale if French not available
            pass
    
    now = datetime.datetime.now()
    
    # Format with seconds and French date
    time_str = now.strftime("%H:%M:%S")
    
    # Try to get French date format, fallback to English if needed
    try:
        date_str = now.strftime("%A %d %B %Y")
    except:
        date_str = now.strftime("%A %d %B %Y")
    
    return {
        "text": time_str,
        "tooltip": date_str.title(),
        "class": "calendar"
    }

if __name__ == "__main__":
    print(json.dumps(get_french_date()))
