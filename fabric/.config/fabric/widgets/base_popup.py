"""
Base Popup Widget
Provides common functionality for all popup widgets:
- Blur background
- Animated open/close
- Single widget at a time
- Position near button
"""

from fabric.widgets.wayland import WaylandWindow
from gi.repository import GLib


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

        # Store original margin for animation
        self._original_margin = margin

        # Track if we're open (simple flag, no complex state management)
        self._is_open = False

        # Animation state
        self._animation_progress = 0.0
        self._animation_timeout_id = None
        self._animation_slide_distance = 30  # Slide down 30px (more visible)
        self._animation_duration_ms = 400  # 400ms duration (slower)

        # Build content directly (no revealer wrapper)
        content = self.build_content()
        self.add(content)

        # Add blur style class
        self.add_style_class("popup-blur")

    def build_content(self):
        """Override this method in subclasses to build popup content"""
        from fabric.widgets.label import Label
        return Label(label="Base Popup Widget")

    def toggle(self):
        """Toggle popup visibility"""
        print(f"[TOGGLE] _is_open={self._is_open}")
        if self._is_open:
            self.close()
        else:
            self.open()

    def open(self):
        """Open popup"""
        print(f"[OPEN] Called, _is_open={self._is_open}")
        self._is_open = True
        print(f"[OPEN] Setting _is_open=True")

        # Register with popup manager (closes other popups)
        popup_manager.register_popup(self)

        # Refresh content before showing
        self.on_open()

        # Reset animation state
        self._animation_progress = 0.0

        # Parse original margin to get the target top margin
        parts = self._original_margin.split()
        if len(parts) == 4:
            self._target_top_margin = int(parts[0].replace('px', ''))
        else:
            self._target_top_margin = 50

        # Start above the target position
        start_margin = self._target_top_margin - self._animation_slide_distance
        print(f"[ANIMATION] Starting at {start_margin}px, target {self._target_top_margin}px")
        self._update_animation_margin(start_margin)

        # Show all content first to get proper sizing
        content = self.get_child()
        if content:
            content.show_all()

        # Hide children with opacity (they still take space)
        self._children_to_reveal = self._hide_and_collect_children()
        self._current_reveal_index = 0

        # Set fixed width to prevent horizontal resizing
        self.set_size_request(self.popup_width, -1)

        # Show window itself (children are invisible but taking space)
        self.show()

        # Start animation and progressive content reveal simultaneously
        GLib.idle_add(self._start_slide_animation)

        # Start revealing content during slide (with a small initial delay)
        if self._children_to_reveal:
            GLib.timeout_add(150, self._reveal_next_child_during_slide)

    def _start_slide_animation(self):
        """Start the slide-down animation"""
        if self._animation_timeout_id:
            GLib.source_remove(self._animation_timeout_id)

        self._animation_start_time = GLib.get_monotonic_time()
        self._animation_timeout_id = GLib.timeout_add(16, self._animate_slide_frame)  # ~60 FPS
        return False

    def _animate_slide_frame(self):
        """Animate one frame of the slide-down effect"""
        if not self._is_open:
            self._animation_timeout_id = None
            return False

        # Calculate progress (0.0 to 1.0)
        elapsed_ms = (GLib.get_monotonic_time() - self._animation_start_time) / 1000
        progress = min(1.0, elapsed_ms / self._animation_duration_ms)

        # Apply easing (ease-out)
        eased_progress = 1 - (1 - progress) ** 3

        # Calculate current margin (interpolate from start to target)
        start_margin = self._target_top_margin - self._animation_slide_distance
        current_margin = start_margin + (self._animation_slide_distance * eased_progress)
        self._update_animation_margin(int(current_margin))

        # Debug every frame to see if loop is running
        print(f"[ANIMATION] Frame - Progress: {progress:.3f}, Elapsed: {elapsed_ms:.1f}ms, Margin: {int(current_margin)}px")

        # Continue or finish animation
        if progress >= 1.0:
            self._animation_timeout_id = None
            print(f"[ANIMATION] Complete")
            return False

        return True  # Continue animation

    def _hide_and_collect_children(self):
        """Hide all children and return them as a list for progressive reveal"""
        content = self.get_child()
        if not content or not hasattr(content, 'get_children'):
            return []

        children = content.get_children()
        for child in children:
            # Keep them visible so they take up space, but make them invisible
            child.set_opacity(0)

        print(f"[CONTENT] Collected {len(children)} children for progressive reveal")
        return list(children)

    def _reveal_next_child_during_slide(self):
        """Reveal next child during the slide animation"""
        if not self._is_open or not self._children_to_reveal:
            return False

        if self._current_reveal_index >= len(self._children_to_reveal):
            print(f"[CONTENT REVEAL] All {len(self._children_to_reveal)} elements revealed")
            return False

        # Fade in the next child (already taking up space, just invisible)
        child = self._children_to_reveal[self._current_reveal_index]
        print(f"[CONTENT REVEAL] Revealing element {self._current_reveal_index + 1}/{len(self._children_to_reveal)}")

        # Animate opacity from 0 to 1 (child already has its size allocated)
        self._animate_child_opacity(child, 0.0, 1.0, 200)

        self._current_reveal_index += 1

        # Schedule next child reveal with longer delay
        if self._current_reveal_index < len(self._children_to_reveal):
            GLib.timeout_add(150, self._reveal_next_child_during_slide)
            return False

        return False

    def _animate_child_opacity(self, child, start_opacity, end_opacity, duration_ms):
        """Animate a child's opacity"""
        start_time = GLib.get_monotonic_time()

        def animate_frame():
            if not self._is_open:
                return False

            elapsed_ms = (GLib.get_monotonic_time() - start_time) / 1000
            progress = min(1.0, elapsed_ms / duration_ms)

            current_opacity = start_opacity + (end_opacity - start_opacity) * progress
            child.set_opacity(current_opacity)

            return progress < 1.0

        GLib.timeout_add(16, animate_frame)

    def _update_animation_margin(self, margin_top):
        """Update the window margin for animation"""
        # Parse original margin to keep other values
        parts = self._original_margin.split()
        if len(parts) == 4:
            new_margin = f"{margin_top}px {parts[1]} {parts[2]} {parts[3]}"
        else:
            new_margin = f"{margin_top}px 20px 0px 0px"

        self.set_margin(new_margin)

    def close(self):
        """Close popup with slide-up animation"""
        print(f"[CLOSE] Called, _is_open={self._is_open}")
        self._is_open = False
        print(f"[CLOSE] Setting _is_open=False")

        # Stop opening animation if running
        if self._animation_timeout_id:
            GLib.source_remove(self._animation_timeout_id)
            self._animation_timeout_id = None

        # Call on_close hook for cleanup
        self.on_close()

        # Start slide-up closing animation
        GLib.idle_add(self._start_close_animation)

    def _start_close_animation(self):
        """Start the slide-up closing animation"""
        # Parse original margin to get the current top margin
        parts = self._original_margin.split()
        if len(parts) == 4:
            self._target_top_margin = int(parts[0].replace('px', ''))
        else:
            self._target_top_margin = 50

        self._animation_start_time = GLib.get_monotonic_time()
        self._animation_timeout_id = GLib.timeout_add(16, self._animate_close_frame)  # ~60 FPS
        return False

    def _animate_close_frame(self):
        """Animate one frame of the slide-up closing effect"""
        # Use shorter duration for closing (feels snappier)
        close_duration_ms = self._animation_duration_ms * 0.6  # 60% of opening duration

        # Calculate progress (0.0 to 1.0)
        elapsed_ms = (GLib.get_monotonic_time() - self._animation_start_time) / 1000
        progress = min(1.0, elapsed_ms / close_duration_ms)

        # Apply same ease-out for natural feel
        eased_progress = 1 - (1 - progress) ** 3

        # Calculate current margin (interpolate from target to above)
        current_margin = self._target_top_margin - (self._animation_slide_distance * eased_progress)
        self._update_animation_margin(int(current_margin))

        # Debug every frame
        print(f"[CLOSE ANIM] Frame - Progress: {progress:.3f}, Elapsed: {elapsed_ms:.1f}ms, Margin: {int(current_margin)}px")

        # Continue or finish animation
        if progress >= 1.0:
            self._animation_timeout_id = None
            print(f"[CLOSE ANIM] Complete - hiding window")
            # Actually hide the window now
            self.hide()
            popup_manager.unregister_popup(self)
            return False

        return True  # Continue animation

    def close_immediate(self):
        """Close immediately without animation (used when opening another popup)"""
        self._is_open = False

        # Stop animation if running
        if self._animation_timeout_id:
            GLib.source_remove(self._animation_timeout_id)
            self._animation_timeout_id = None

        self.hide()
        popup_manager.unregister_popup(self)

    def on_open(self):
        """
        Called when popup is about to open
        Override this in subclasses to refresh content
        """
        pass

    def on_close(self):
        """
        Called when popup is about to close (before animation)
        Override this in subclasses to cleanup (stop timers, collapse content, etc.)
        """
        pass

    def rebuild_content(self):
        """
        Rebuild the popup content
        Override this in subclasses if content needs to be rebuilt
        """
        # Remove old content
        old_child = self.get_child()
        if old_child:
            self.remove(old_child)

        # Build new content and add directly
        content = self.build_content()
        self.add(content)

        # Show new content if popup is open
        if self._is_open:
            content.show_all()
