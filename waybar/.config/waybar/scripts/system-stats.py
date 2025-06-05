#!/home/athoms/.config/waybar/waybar-env/bin/python
import psutil
import json

def get_system_stats():
    """Get system statistics"""
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Get temperatures (if available)
        temp_info = ""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        temp = entries[0].current
                        temp_info = f"🌡️ {temp:.0f}°C"
                        break
        except:
            pass
        
        # Create tooltip
        tooltip_lines = [
            f"💻 CPU: {cpu_percent:.1f}%",
            f"🧠 RAM: {memory_percent:.1f}% ({memory_used_gb:.1f}/{memory_total_gb:.1f} GB)",
            f"💾 Disk: {disk_percent:.1f}% ({disk_used_gb:.0f}/{disk_total_gb:.0f} GB)"
        ]
        
        if temp_info:
            tooltip_lines.append(temp_info)
        
        # Determine CSS class based on highest usage
        max_usage = max(cpu_percent, memory_percent, disk_percent)
        if max_usage > 90:
            css_class = "critical"
        elif max_usage > 70:
            css_class = "warning"
        else:
            css_class = "normal"
        
        return json.dumps({
            "text": f"{cpu_percent:.0f}%",
            "class": css_class,
            "tooltip": "\n".join(tooltip_lines)
        })
        
    except Exception as e:
        return json.dumps({
            "text": "ERR",
            "class": "error",
            "tooltip": f"System error: {str(e)}"
        })

if __name__ == "__main__":
    print(get_system_stats())
