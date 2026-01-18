"""
Base Popup Widget
Provides common functionality for all popup widgets:
- Blur background
- Animated open/close using GTK Revealer (like ax-shell)
- Single widget at a time
- Position near button
"""

from fabric.widgets.wayland import WaylandWindow
from fabric.widgets.box import Box
from fabric.widgets.revealer import Revealer

from services.config import get_config


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


popup_manager = PopupManager()


class BasePopup(WaylandWindow):
    """
    Base class for all popup widgets

    Features:
    - Blur background (via CSS)
    - Native GTK Revealer animation (slide + fade)
    - CSS transitions for polish
    - Automatic single-popup management
    - Position near button on bar
    """

    def __init__(
        self,
        name="popup-widget",
        anchor="top right",
        margin=None,
        width=None,
        transition_type="slide-down",
        **kwargs
    ):
        config = get_config()

        if margin is None:
            margin = f"{config.popup_margin_top}px {config.popup_margin_right}px 0px 0px"
        if width is None:
            width = config.popup_width

        super().__init__(
            layer="overlay",
            anchor=anchor,
            margin=margin,
            keyboard_mode="on-demand",
            name=name,
            visible=False,
            **kwargs
        )

        self.config = config
        self.popup_width = width
        self._is_open = False
        self._animation_duration_ms = config.animation_duration

        # Build content
        content = self.build_content()

        # Content wrapper with CSS transition support
        self.content_box = Box(
            name=f"{name}-content",
            orientation="v",
            children=[content] if content else [],
        )
        self.content_box.add_style_class("popup-content")

        # Revealer for native GTK animation
        self.revealer = Revealer(
            name=f"{name}-revealer",
            transition_type=transition_type,
            transition_duration=self._animation_duration_ms,
            child=self.content_box,
            child_revealed=False,
        )

        # Outer container for blur and styling
        self.outer_box = Box(
            name=f"{name}-outer",
            orientation="v",
            children=[self.revealer],
        )
        self.outer_box.add_style_class("popup-blur")

        self.add(self.outer_box)
        self.set_size_request(width, -1)

        # Connect revealer state change for cleanup
        self.revealer.connect("notify::child-revealed", self._on_reveal_state_changed)

    def build_content(self):
        """Override this method in subclasses to build popup content"""
        from fabric.widgets.label import Label
        return Label(label="Base Popup Widget")

    def toggle(self):
        """Toggle popup visibility"""
        if self._is_open:
            self.close()
        else:
            self.open()

    def open(self):
        """Open popup with Revealer animation"""
        if self._is_open:
            return

        self._is_open = True
        popup_manager.register_popup(self)
        self.on_open()

        # Show window first, then reveal content
        self.show_all()
        self.revealer.set_reveal_child(True)

        # Add open style class for CSS transitions
        self.content_box.add_style_class("open")

    def close(self):
        """Close popup with Revealer animation"""
        if not self._is_open:
            return

        self._is_open = False
        self.on_close()

        # Remove open style class
        self.content_box.remove_style_class("open")

        # Start revealer close animation
        self.revealer.set_reveal_child(False)

    def _on_reveal_state_changed(self, revealer, _pspec):
        """Called when revealer animation completes"""
        if not revealer.get_child_revealed() and not self._is_open:
            # Animation finished closing - hide window
            self.hide()
            popup_manager.unregister_popup(self)

    def close_immediate(self):
        """Close immediately without animation"""
        self._is_open = False
        self.content_box.remove_style_class("open")
        self.revealer.set_reveal_child(False)
        self.hide()
        popup_manager.unregister_popup(self)

    def on_open(self):
        """Override in subclasses to refresh content"""
        pass

    def on_close(self):
        """Override in subclasses for cleanup"""
        pass

    def rebuild_content(self):
        """Rebuild the popup content"""
        # Remove old content
        for child in self.content_box.get_children():
            self.content_box.remove(child)

        # Build and add new content
        content = self.build_content()
        if content:
            self.content_box.add(content)

        if self._is_open:
            self.content_box.show_all()
