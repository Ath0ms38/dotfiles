#!/usr/bin/env python3
import subprocess
import psutil

def show_battery_popup():
    """Show battery information popup"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = battery.power_plugged
            time_left = battery.secsleft
            
            status = "🔌 Charging" if plugged else "🔋 On Battery"
            
            info_lines = [
                f"Battery: {percent:.0f}%",
                f"Status: {status}"
            ]
            
            if time_left != psutil.POWER_TIME_UNLIMITED and time_left > 0:
                hours = time_left // 3600
                minutes = (time_left % 3600) // 60
                info_lines.append(f"Time: {hours}h {minutes}m")
            
            subprocess.run([
                'notify-send',
                '-t', '4000',
                '🔋 Battery Information',
                '\n'.join(info_lines)
            ])
        else:
            subprocess.run([
                'notify-send',
                '-t', '3000',
                '🔋 Battery',
                'No battery detected'
            ])
        
    except Exception as e:
        subprocess.run([
            'notify-send',
            '-t', '3000',
            'Battery Error',
            str(e)
        ])

if __name__ == "__main__":
    show_battery_popup()
