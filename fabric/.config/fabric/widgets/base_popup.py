"""
Base Popup Widget
Provides common functionality for all popup widgets:
- Blur background
- Animated open/close
- Single widget at a time
- Position near button
"""

from fabric.widgets.wayland import WaylandWindow
from fabric.widgets.revealer import Revealer
from gi.repository import Gtk, GLib


# Global widget manager to ensure only one popup is open at a time
class PopupManager:
    """Manages popup widgets to ensure only one is visible at a time"""

    def __init__(self):
        self.current_popup = None

    def register_popup(self, popup):
        """Register a popup and close any currently open popup"""
        if self.current_popup and self.current_popup != popup:
            self.current_popup.close_immediate()
        self.current_popup = popup

    def unregister_popup(self, popup):
        """Unregister a popup when it closes"""
        if self.current_popup == popup:
            self.current_popup = None


# Global popup manager instance
popup_manager = PopupManager()


class BasePopup(WaylandWindow):
    """
    Base class for all popup widgets

    Features:
    - Blur background (via CSS)
    - Animated slide-down open/close
    - Automatic single-popup management
    - Position near button on bar
    """

    def __init__(
        self,
        name="popup-widget",
        anchor="top right",
        margin="50px 20px 0px 0px",
        width=400,
        **kwargs
    ):
        super().__init__(
            layer="overlay",
            anchor=anchor,
            margin=margin,
            keyboard_mode="on-demand",
            name=name,
            visible=False,
            **kwargs
        )

        # Store width for sizing
        self.popup_width = width

        # Animation state
        self.is_animating = False
        self.animation_timeout_id = None

        # Create revealer for animation
        self.revealer = Revealer(
            transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
            transition_duration=250,  # 250ms animation
            reveal_child=False
        )

        # Build content (to be overridden by subclasses)
        content = self.build_content()
        self.revealer.add(content)

        # Set revealer as child
        self.add(self.revealer)

        # Add blur style class
        self.add_style_class("popup-blur")

    def build_content(self):
        """Override this method in subclasses to build popup content"""
        from fabric.widgets.label import Label
        return Label(label="Base Popup Widget")

    def toggle(self):
        """Toggle popup visibility with animation"""
        if self.get_visible():
            self.close()
        else:
            self.open()

    def open(self):
        """Open popup with animation"""
        if self.is_animating:
            return

        # Register with popup manager (closes other popups)
        popup_manager.register_popup(self)

        # Refresh content before showing
        self.on_open()

        # Show window
        self.show_all()

        # Start reveal animation
        self.is_animating = True
        GLib.idle_add(self._start_reveal_animation)

    def _start_reveal_animation(self):
        """Start the reveal animation (called from idle)"""
        self.revealer.set_reveal_child(True)

        # Mark animation as complete after transition duration
        self.animation_timeout_id = GLib.timeout_add(
            300,  # Slightly longer than transition for safety
            self._on_animation_complete
        )
        return False

    def _on_animation_complete(self):
        """Called when animation completes"""
        self.is_animating = False
        self.animation_timeout_id = None
        return False

    def close(self):
        """Close popup with animation"""
        if self.is_animating:
            return

        # Start hide animation
        self.is_animating = True
        self.revealer.set_reveal_child(False)

        # Hide window after animation completes
        self.animation_timeout_id = GLib.timeout_add(
            300,  # Wait for animation
            self._finish_close
        )

    def _finish_close(self):
        """Finish closing after animation"""
        self.hide()
        self.is_animating = False
        self.animation_timeout_id = None
        popup_manager.unregister_popup(self)
        return False

    def close_immediate(self):
        """Close immediately without animation (used when opening another popup)"""
        if self.animation_timeout_id:
            GLib.source_remove(self.animation_timeout_id)
            self.animation_timeout_id = None

        self.revealer.set_reveal_child(False)
        self.hide()
        self.is_animating = False

    def on_open(self):
        """
        Called when popup is about to open
        Override this in subclasses to refresh content
        """
        pass

    def rebuild_content(self):
        """
        Rebuild the popup content
        Override this in subclasses if content needs to be rebuilt
        """
        # Remove old content
        old_child = self.revealer.get_child()
        if old_child:
            self.revealer.remove(old_child)

        # Build new content
        content = self.build_content()
        self.revealer.add(content)

        # Show new content if revealer is revealed
        if self.revealer.get_reveal_child():
            content.show_all()
