"""
Animator Service
Based directly on Ax-Shell's proven animation system.
"""

from fabric.core.service import Service, Signal, Property
from gi.repository import GLib, Gtk
from typing import Optional


class Animator(Service):
    """
    Animation service with cubic bezier easing.
    Uses Bernstein polynomial for bezier interpolation.
    """

    @Signal
    def finished(self) -> None:
        ...

    # Common easing curves (x1, y1, x2, y2)
    EASE_LINEAR = (0.0, 0.0, 1.0, 1.0)
    EASE_IN = (0.42, 0.0, 1.0, 1.0)
    EASE_OUT = (0.0, 0.0, 0.58, 1.0)
    EASE_IN_OUT = (0.42, 0.0, 0.58, 1.0)
    EASE_OUT_CUBIC = (0.215, 0.61, 0.355, 1.0)
    EASE_OUT_BACK = (0.175, 0.885, 0.32, 1.275)
    EASE_OUT_EXPO = (0.19, 1.0, 0.22, 1.0)
    EASE_IN_OUT_CUBIC = (0.645, 0.045, 0.355, 1.0)

    @Property(float, "read-write", default_value=0.0)
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float):
        self._value = value

    @Property(float, "read-write", default_value=1.0)
    def max_value(self) -> float:
        return self._max_value

    @max_value.setter
    def max_value(self, value: float):
        self._max_value = value

    @Property(float, "read-write", default_value=0.0)
    def min_value(self) -> float:
        return self._min_value

    @min_value.setter
    def min_value(self, value: float):
        self._min_value = value

    @Property(bool, "read-write", default_value=False)
    def playing(self) -> bool:
        return self._playing

    @playing.setter
    def playing(self, value: bool):
        self._playing = value

    @Property(bool, "read-write", default_value=False)
    def repeat(self) -> bool:
        return self._repeat

    @repeat.setter
    def repeat(self, value: bool):
        self._repeat = value

    def __init__(
        self,
        bezier_curve: tuple = None,
        duration: float = 0.4,
        min_value: float = 0.0,
        max_value: float = 1.0,
        repeat: bool = False,
        tick_widget: Optional[Gtk.Widget] = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self._bezier_curve = bezier_curve or self.EASE_OUT_CUBIC
        self._duration = duration
        self._value = min_value
        self._min_value = min_value
        self._max_value = max_value
        self._repeat = repeat
        self._playing = False

        self._start_time = None
        self._tick_handler = None
        self._timeline_pos = 0.0
        self._tick_widget = tick_widget

    @property
    def bezier_curve(self) -> tuple:
        return self._bezier_curve

    @bezier_curve.setter
    def bezier_curve(self, value: tuple):
        self._bezier_curve = value

    @property
    def duration(self) -> float:
        return self._duration

    @duration.setter
    def duration(self, value: float):
        self._duration = max(0.001, value)

    def _get_time_now(self) -> float:
        return GLib.get_monotonic_time() / 1_000_000

    def _lerp(self, start: float, end: float, t: float) -> float:
        return start + (end - start) * t

    def _interpolate_cubic_bezier(self, t: float) -> float:
        """Bernstein polynomial - the correct way"""
        y_points = (0, self._bezier_curve[1], self._bezier_curve[3], 1)
        return (
            (1 - t) ** 3 * y_points[0]
            + 3 * (1 - t) ** 2 * t * y_points[1]
            + 3 * (1 - t) * t ** 2 * y_points[2]
            + t ** 3 * y_points[3]
        )

    def _ease(self, t: float) -> float:
        return self._lerp(
            self._min_value,
            self._max_value,
            self._interpolate_cubic_bezier(t)
        )

    def _update_value(self, current_time: float) -> None:
        if not self._playing:
            return

        elapsed = current_time - self._start_time
        self._timeline_pos = min(1.0, elapsed / self._duration)
        self.value = self._ease(self._timeline_pos)

        if self._timeline_pos >= 1.0:
            if self._repeat:
                self._start_time = current_time
                self._timeline_pos = 0.0
            else:
                self.value = self._max_value
                self.finished()
                self.pause()

    def _handle_tick(self, *_) -> bool:
        self._update_value(self._get_time_now())
        return True

    def _remove_tick_handlers(self) -> None:
        if self._tick_handler:
            if self._tick_widget:
                self._tick_widget.remove_tick_callback(self._tick_handler)
            else:
                GLib.source_remove(self._tick_handler)
        self._tick_handler = None

    def play(self) -> None:
        if self._playing:
            return

        self._start_time = self._get_time_now()

        if not self._tick_handler:
            if self._tick_widget:
                self._tick_handler = self._tick_widget.add_tick_callback(
                    self._handle_tick
                )
            else:
                self._tick_handler = GLib.timeout_add(16, self._handle_tick)

        self._playing = True

    def start(self) -> None:
        """Alias for play()"""
        self.play()

    def pause(self) -> None:
        self._playing = False
        self._remove_tick_handlers()

    def stop(self) -> None:
        self._remove_tick_handlers()
        self._timeline_pos = 0.0
        self._playing = False
        self.value = self._min_value


class AnimationGroup:
    """Manages multiple animators running together."""

    def __init__(self):
        self._animators: list[Animator] = []
        self._finished_count = 0
        self._on_all_finished = None

    def add(self, animator: Animator) -> None:
        self._animators.append(animator)
        animator.connect("finished", self._on_animator_finished)

    def start(self, on_all_finished: callable = None) -> None:
        self._finished_count = 0
        self._on_all_finished = on_all_finished
        for animator in self._animators:
            animator.play()

    def stop(self) -> None:
        for animator in self._animators:
            animator.stop()

    def _on_animator_finished(self, animator) -> None:
        self._finished_count += 1
        if self._finished_count >= len(self._animators) and self._on_all_finished:
            self._on_all_finished()


def animate_property(
    widget,
    property_setter: callable,
    start_value: float,
    end_value: float,
    duration: float = 0.4,
    easing: tuple = Animator.EASE_OUT_CUBIC,
    on_finished: callable = None,
    tick_widget: Optional[Gtk.Widget] = None
) -> Animator:
    """Convenience function to animate a property."""
    _tick_widget = tick_widget or (widget if isinstance(widget, Gtk.Widget) else None)

    animator = Animator(
        duration=duration,
        bezier_curve=easing,
        min_value=start_value,
        max_value=end_value,
        tick_widget=_tick_widget
    )

    def on_value_changed(anim, _pspec):
        property_setter(anim.value)

    animator.connect("notify::value", on_value_changed)

    if on_finished:
        animator.connect("finished", lambda a: on_finished())

    animator.play()
    return animator
