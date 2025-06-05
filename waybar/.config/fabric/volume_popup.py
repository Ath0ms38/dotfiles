#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import subprocess
import re
import sys
import os

class VolumePopup:
    def __init__(self):
        self.window = None
        self.volume_scale = None
        self.volume_label = None
        self.mute_button = None
        self.is_muted = False
        self.current_volume = 0
        
    def get_volume_info(self):
        """Get current volume and mute status"""
        try:
            result = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], 
                                  capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            
            # Parse volume
            volume_match = re.search(r'Volume: ([\d.]+)', output)
            self.is_muted = '[MUTED]' in output
            
            if volume_match:
                self.current_volume = int(float(volume_match.group(1)) * 100)
            else:
                self.current_volume = 0
                
        except Exception as e:
            print(f"Error getting volume: {e}")
            self.current_volume = 0
            self.is_muted = False
    
    def set_volume(self, volume):
        """Set system volume"""
        try:
            subprocess.run(['wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', f'{volume}%'], 
                         check=True)
        except Exception as e:
            print(f"Error setting volume: {e}")
    
    def toggle_mute(self):
        """Toggle mute status"""
        try:
            subprocess.run(['wpctl', 'set-mute', '@DEFAULT_AUDIO_SINK@', 'toggle'], 
                         check=True)
            self.get_volume_info()
            self.update_ui()
        except Exception as e:
            print(f"Error toggling mute: {e}")
    
    def on_volume_changed(self, scale):
        """Handle volume scale changes"""
        volume = int(scale.get_value())
        self.set_volume(volume)
        self.volume_label.set_text(f"{volume}%")
    
    def on_mute_clicked(self, button):
        """Handle mute button click"""
        self.toggle_mute()
    
    def update_ui(self):
        """Update UI elements"""
        if self.volume_scale:
            self.volume_scale.set_value(self.current_volume)
        if self.volume_label:
            if self.is_muted:
                self.volume_label.set_text(f"{self.current_volume}% (Muted)")
            else:
                self.volume_label.set_text(f"{self.current_volume}%")
        if self.mute_button:
            if self.is_muted:
                self.mute_button.set_label("🔇 Unmute")
            else:
                self.mute_button.set_label("🔊 Mute")
    
    def create_window(self):
        """Create the popup window"""
        self.window = Gtk.Window()
        self.window.set_title("Volume Control")
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_keep_above(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        
        # Set window properties
        self.window.set_default_size(300, 120)
        self.window.set_resizable(False)
        
        # Position window at center of screen
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        
        # Center the popup
        popup_x = (geometry.width - 300) // 2
        popup_y = (geometry.height - 120) // 2
        self.window.move(popup_x, popup_y)
        
        # Create main container
        main_box = Gtk.VBox(spacing=10)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(15)
        main_box.set_margin_bottom(15)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<b>🔊 Volume Control</b>")
        title.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(title, False, False, 0)
        
        # Volume info
        self.volume_label = Gtk.Label()
        self.volume_label.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(self.volume_label, False, False, 0)
        
        # Volume scale
        self.volume_scale = Gtk.HScale()
        self.volume_scale.set_range(0, 100)
        self.volume_scale.set_value(self.current_volume)
        self.volume_scale.set_digits(0)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        main_box.pack_start(self.volume_scale, False, False, 0)
        
        # Mute button
        self.mute_button = Gtk.Button()
        self.mute_button.connect("clicked", self.on_mute_clicked)
        self.mute_button.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(self.mute_button, False, False, 0)
        
        # Style the window
        css_provider = Gtk.CssProvider()
        css_data = """
        window {
            background: rgba(13, 17, 23, 0.95);
            border: 2px solid rgba(139, 233, 253, 0.6);
            border-radius: 12px;
            color: #e6edf3;
        }
        label {
            color: #e6edf3;
            font-weight: 600;
        }
        scale {
            color: #8bf5fd;
        }
        scale trough {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 6px;
        }
        scale highlight {
            background: linear-gradient(to right, #8bf5fd, #bb9af7);
            border-radius: 6px;
        }
        button {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(139, 233, 253, 0.4);
            border-radius: 8px;
            color: #e6edf3;
            padding: 8px 16px;
        }
        button:hover {
            background: rgba(139, 233, 253, 0.3);
            border-color: rgba(139, 233, 253, 0.6);
        }
        """
        css_provider.load_from_data(css_data.encode())
        
        style_context = self.window.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        self.window.add(main_box)
        self.update_ui()
        
        # Auto-close after 5 seconds or on focus loss
        GLib.timeout_add_seconds(5, self.close_popup)
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
        self.get_volume_info()
        self.create_window()
        self.window.show_all()
        self.window.grab_focus()
        Gtk.main()

def main():
    popup = VolumePopup()
    popup.show()

if __name__ == "__main__":
    main()
