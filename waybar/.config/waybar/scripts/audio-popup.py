#!/home/athoms/.config/waybar/waybar-env/bin/python
import subprocess
import sys
import time

def show_audio_popup():
    """Show audio volume popup using notify-send"""
    try:
        # Get current volume
        result = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], 
                              capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        
        # Parse volume
        import re
        volume_match = re.search(r'Volume: ([\d.]+)', output)
        is_muted = '[MUTED]' in output
        
        if volume_match:
            volume = float(volume_match.group(1))
            volume_percent = int(volume * 100)
        else:
            volume_percent = 0
        
        # Create volume bar
        bar_length = 20
        filled_blocks = int((volume_percent / 100) * bar_length)
        volume_bar = "█" * filled_blocks + "░" * (bar_length - filled_blocks)
        
        # Create notification
        if is_muted:
            title = "🔇 Audio Muted"
            body = f"{volume_bar} {volume_percent}%"
        else:
            title = "🔊 Volume"
            body = f"{volume_bar} {volume_percent}%"
        
        # Show notification
        subprocess.run([
            'notify-send', 
            '-t', '2000',
            '-h', 'string:synchronous:volume',
            '-h', f'int:value:{volume_percent}',
            title, body
        ])
        
    except Exception as e:
        subprocess.run([
            'notify-send', 
            '-t', '2000',
            'Audio Error', 
            str(e)
        ])

if __name__ == "__main__":
    show_audio_popup()
