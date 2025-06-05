#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import psutil

def show_system_popup():
    """Show system information popup"""
    try:
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Format the information
        info_lines = [
            f"💻 CPU Usage: {cpu_percent:.1f}%",
            f"🧠 RAM: {memory.percent:.1f}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)",
            f"💾 Disk: {disk.percent:.1f}% ({disk.used / (1024**3):.0f}GB / {disk.total / (1024**3):.0f}GB)",
        ]
        
        # Add temperature if available
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        temp = entries[0].current
                        info_lines.append(f"🌡️ Temperature: {temp:.0f}°C")
                        break
        except:
            pass
        
        # Show notification
        subprocess.run([
            'notify-send',
            '-t', '5000',
            '💻 System Information',
            '\n'.join(info_lines)
        ])
        
    except Exception as e:
        subprocess.run([
            'notify-send',
            '-t', '3000', 
            'System Error',
            str(e)
        ])

if __name__ == "__main__":
    show_system_popup()
