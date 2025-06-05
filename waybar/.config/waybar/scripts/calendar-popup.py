#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import datetime
import locale

def show_calendar_popup():
    """Show calendar popup"""
    try:
        # Set French locale
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        except:
            pass
        
        now = datetime.datetime.now()
        
        # Format date information
        date_info = [
            f"📅 {now.strftime('%A %d %B %Y')}",
            f"🕐 {now.strftime('%H:%M:%S')}",
            f"📆 Semaine {now.isocalendar()[1]}"
        ]
        
        subprocess.run([
            'notify-send',
            '-t', '5000',
            '📅 Date et Heure',
            '\n'.join(date_info)
        ])
        
    except Exception as e:
        subprocess.run([
            'notify-send',
            '-t', '3000',
            'Calendar Error',
            str(e)
        ])

if __name__ == "__main__":
    show_calendar_popup()
