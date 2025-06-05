#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import psutil
import subprocess
import sys

class SystemPopup:
    def __init__(self):
        self.window = None
        
    def get_system_info(self):
        """Get comprehensive system information"""
        info = {}
        
        try:
            # CPU information
            info['cpu_percent'] = psutil.cpu_percent(interval=1)
            info['cpu_count'] = psutil.cpu_count()
            info['cpu_freq'] = psutil.cpu_freq()
            
            # Memory information
            memory = psutil.virtual_memory()
            info['memory_percent'] = memory.percent
            info['memory_used'] = memory.used / (1024**3)  # GB
            info['memory_total'] = memory.total / (1024**3)  # GB
            info['memory_available'] = memory.available / (1024**3)  # GB
            
            # Disk information
            disk = psutil.disk_usage('/')
            info['disk_percent'] = disk.percent
            info['disk_used'] = disk.used / (1024**3)  # GB
            info['disk_total'] = disk.total / (1024**3)  # GB
            info['disk_free'] = disk.free / (1024**3)  # GB
            
            # Network information
            net_io = psutil.net_io_counters()
            info['bytes_sent'] = net_io.bytes_sent / (1024**2)  # MB
            info['bytes_recv'] = net_io.bytes_recv / (1024**2)  # MB
            
            # Temperature (if available)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            info['temperature'] = entries[0].current
                            break
            except:
                info['temperature'] = None
                
            # Boot time
            info['boot_time'] = psutil.boot_time()
            
            # Process count
            info['process_count'] = len(psutil.pids())
            
        except Exception as e:
            print(f"Error getting system info: {e}")
            
        return info
    
    def format_uptime(self, boot_time):
        """Format uptime string"""
        import time
        uptime_seconds = time.time() - boot_time
        days = int(uptime_seconds // (24 * 3600))
        hours = int((uptime_seconds % (24 * 3600)) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_status_color(self, percentage):
        """Get color based on usage percentage"""
        if percentage > 90:
            return "#f87171"  # Red
        elif percentage > 70:
            return "#fbbf24"  # Yellow
        elif percentage > 50:
            return "#fb923c"  # Orange
        else:
            return "#22c55e"  # Green
    
    def create_progress_bar(self, percentage, color):
        """Create a progress bar widget"""
        progress = Gtk.ProgressBar()
        progress.set_fraction(percentage / 100.0)
        progress.set_show_text(True)
        progress.set_text(f"{percentage:.1f}%")
        
        # Apply color styling
        css_provider = Gtk.CssProvider()
        css_data = f"""
        progressbar {{
            min-height: 20px;
        }}
        progressbar trough {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 10px;
        }}
        progressbar progress {{
            background: {color};
            border-radius: 10px;
        }}
        progressbar text {{
            color: #e6edf3;
            font-weight: bold;
        }}
        """
        css_provider.load_from_data(css_data.encode())
        progress.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        return progress
    
    def create_info_row(self, label, value, detail=None):
        """Create an information row"""
        box = Gtk.HBox(spacing=10)
        
        # Label
        label_widget = Gtk.Label()
        label_widget.set_markup(f"<b>{label}:</b>")
        label_widget.set_halign(Gtk.Align.START)
        label_widget.set_size_request(100, -1)
        box.pack_start(label_widget, False, False, 0)
        
        # Value
        value_widget = Gtk.Label(value)
        value_widget.set_halign(Gtk.Align.START)
        value_widget.set_hexpand(True)
        box.pack_start(value_widget, True, True, 0)
        
        # Detail (if provided)
        if detail:
            detail_widget = Gtk.Label()
            detail_widget.set_markup(f"<small>{detail}</small>")
            detail_widget.set_halign(Gtk.Align.END)
            box.pack_end(detail_widget, False, False, 0)
        
        return box
    
    def create_window(self):
        """Create the popup window"""
        self.window = Gtk.Window()
        self.window.set_title("System Information")
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_keep_above(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        
        # Set window properties
        self.window.set_default_size(400, 500)
        self.window.set_resizable(False)
        
        # Position window at center of screen
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        
        # Center the popup
        popup_x = (geometry.width - 400) // 2
        popup_y = (geometry.height - 500) // 2
        self.window.move(popup_x, popup_y)
        
        # Get system info
        info = self.get_system_info()
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Create main container
        main_box = Gtk.VBox(spacing=15)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(15)
        main_box.set_margin_bottom(15)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<b>💻 System Information</b>")
        title.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(title, False, False, 0)
        
        # CPU Section
        cpu_frame = Gtk.Frame()
        cpu_frame.set_label("🔥 CPU")
        cpu_box = Gtk.VBox(spacing=5)
        cpu_box.set_margin_left(10)
        cpu_box.set_margin_right(10)
        cpu_box.set_margin_top(10)
        cpu_box.set_margin_bottom(10)
        
        # CPU usage bar
        cpu_color = self.get_status_color(info.get('cpu_percent', 0))
        cpu_progress = self.create_progress_bar(info.get('cpu_percent', 0), cpu_color)
        cpu_box.pack_start(cpu_progress, False, False, 0)
        
        # CPU details
        cpu_details = self.create_info_row(
            "Cores", 
            str(info.get('cpu_count', 'N/A')),
            f"{info.get('cpu_freq').current:.0f} MHz" if info.get('cpu_freq') else None
        )
        cpu_box.pack_start(cpu_details, False, False, 0)
        
        cpu_frame.add(cpu_box)
        main_box.pack_start(cpu_frame, False, False, 0)
        
        # Memory Section
        memory_frame = Gtk.Frame()
        memory_frame.set_label("🧠 Memory")
        memory_box = Gtk.VBox(spacing=5)
        memory_box.set_margin_left(10)
        memory_box.set_margin_right(10)
        memory_box.set_margin_top(10)
        memory_box.set_margin_bottom(10)
        
        # Memory usage bar
        memory_color = self.get_status_color(info.get('memory_percent', 0))
        memory_progress = self.create_progress_bar(info.get('memory_percent', 0), memory_color)
        memory_box.pack_start(memory_progress, False, False, 0)
        
        # Memory details
        memory_details = self.create_info_row(
            "Used",
            f"{info.get('memory_used', 0):.1f} GB",
            f"of {info.get('memory_total', 0):.1f} GB"
        )
        memory_box.pack_start(memory_details, False, False, 0)
        
        available_details = self.create_info_row(
            "Available",
            f"{info.get('memory_available', 0):.1f} GB"
        )
        memory_box.pack_start(available_details, False, False, 0)
        
        memory_frame.add(memory_box)
        main_box.pack_start(memory_frame, False, False, 0)
        
        # Disk Section
        disk_frame = Gtk.Frame()
        disk_frame.set_label("💾 Storage")
        disk_box = Gtk.VBox(spacing=5)
        disk_box.set_margin_left(10)
        disk_box.set_margin_right(10)
        disk_box.set_margin_top(10)
        disk_box.set_margin_bottom(10)
        
        # Disk usage bar
        disk_color = self.get_status_color(info.get('disk_percent', 0))
        disk_progress = self.create_progress_bar(info.get('disk_percent', 0), disk_color)
        disk_box.pack_start(disk_progress, False, False, 0)
        
        # Disk details
        disk_details = self.create_info_row(
            "Used",
            f"{info.get('disk_used', 0):.0f} GB",
            f"of {info.get('disk_total', 0):.0f} GB"
        )
        disk_box.pack_start(disk_details, False, False, 0)
        
        free_details = self.create_info_row(
            "Free",
            f"{info.get('disk_free', 0):.0f} GB"
        )
        disk_box.pack_start(free_details, False, False, 0)
        
        disk_frame.add(disk_box)
        main_box.pack_start(disk_frame, False, False, 0)
        
        # System Section
        system_frame = Gtk.Frame()
        system_frame.set_label("ℹ️ System")
        system_box = Gtk.VBox(spacing=5)
        system_box.set_margin_left(10)
        system_box.set_margin_right(10)
        system_box.set_margin_top(10)
        system_box.set_margin_bottom(10)
        
        # Uptime
        uptime_info = self.create_info_row(
            "Uptime",
            self.format_uptime(info.get('boot_time', 0))
        )
        system_box.pack_start(uptime_info, False, False, 0)
        
        # Processes
        process_info = self.create_info_row(
            "Processes",
            str(info.get('process_count', 'N/A'))
        )
        system_box.pack_start(process_info, False, False, 0)
        
        # Temperature
        if info.get('temperature'):
            temp_info = self.create_info_row(
                "Temperature",
                f"{info['temperature']:.0f}°C"
            )
            system_box.pack_start(temp_info, False, False, 0)
        
        # Network
        net_info = self.create_info_row(
            "Network",
            f"↑ {info.get('bytes_sent', 0):.0f} MB",
            f"↓ {info.get('bytes_recv', 0):.0f} MB"
        )
        system_box.pack_start(net_info, False, False, 0)
        
        system_frame.add(system_box)
        main_box.pack_start(system_frame, False, False, 0)
        
        scrolled.add(main_box)
        
        # Style the window
        css_provider = Gtk.CssProvider()
        css_data = """
        window {
            background: rgba(13, 17, 23, 0.95);
            border: 2px solid rgba(139, 233, 253, 0.6);
            border-radius: 12px;
            color: #e6edf3;
        }
        frame {
            border: 1px solid rgba(139, 233, 253, 0.3);
            border-radius: 8px;
            background: rgba(30, 41, 59, 0.4);
        }
        frame > label {
            color: #8bf5fd;
            font-weight: bold;
            padding: 0 8px;
            background: rgba(13, 17, 23, 0.8);
        }
        label {
            color: #e6edf3;
        }
        """
        css_provider.load_from_data(css_data.encode())
        
        style_context = self.window.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        self.window.add(scrolled)
        
        # Auto-close after 10 seconds or on focus loss
        GLib.timeout_add_seconds(10, self.close_popup)
        self.window.connect("focus-out-event", lambda w, e: self.close_popup())
        self.window.connect("key-press-event", self.on_key_press)
        
        return self.window
    
    def on_key_press(self, widget, event):
        """Handle key presses"""
        if event.keyval == Gdk.KEY_Escape:
            self.close_popup()
            return True
        return False
    
    def close_popup(self):
        """Close the popup"""
        if self.window:
            self.window.destroy()
        Gtk.main_quit()
        return False
    
    def show(self):
        """Show the popup"""
        self.create_window()
        self.window.show_all()
        self.window.grab_focus()
        Gtk.main()

def main():
    popup = SystemPopup()
    popup.show()

if __name__ == "__main__":
    main()
