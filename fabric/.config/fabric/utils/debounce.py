"""
Debouncing Utilities
Prevents rapid-fire updates from sliders and other input widgets.

Usage:
    from utils.debounce import Debouncer, debounce

    # Class-based debouncer
    debouncer = Debouncer(delay_ms=50)
    debouncer.call(my_function, arg1, arg2)

    # Decorator-based
    @debounce(delay_ms=100)
    def on_slider_changed(value):
        expensive_update(value)
"""

from gi.repository import GLib
from functools import wraps
from typing import Callable, Any, Optional


class Debouncer:
    """
    Debounces function calls, only executing after a delay with no new calls.

    Example:
        debouncer = Debouncer(delay_ms=100)

        def on_slider_change(scale):
            value = scale.get_value()
            debouncer.call(update_volume, value)
    """

    def __init__(self, delay_ms: int = 50):
        """
        Initialize debouncer.

        Args:
            delay_ms: Delay in milliseconds before executing
        """
        self.delay_ms = delay_ms
        self._timeout_id: Optional[int] = None
        self._pending_func: Optional[Callable] = None
        self._pending_args: tuple = ()
        self._pending_kwargs: dict = {}

    def call(self, func: Callable, *args, **kwargs) -> None:
        """
        Schedule a debounced function call.

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function
        """
        # Cancel any pending call
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

        # Store pending call
        self._pending_func = func
        self._pending_args = args
        self._pending_kwargs = kwargs

        # Schedule execution
        self._timeout_id = GLib.timeout_add(self.delay_ms, self._execute)

    def _execute(self) -> bool:
        """Execute the pending function call"""
        self._timeout_id = None

        if self._pending_func:
            try:
                self._pending_func(*self._pending_args, **self._pending_kwargs)
            except Exception as e:
                print(f"Debounced call failed: {e}")
            finally:
                self._pending_func = None
                self._pending_args = ()
                self._pending_kwargs = {}

        return False  # Don't repeat

    def cancel(self) -> None:
        """Cancel any pending call"""
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
            self._pending_func = None

    def flush(self) -> None:
        """Execute pending call immediately"""
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
            self._execute()


def debounce(delay_ms: int = 50):
    """
    Decorator to debounce a function.

    Example:
        @debounce(delay_ms=100)
        def update_volume(value):
            set_system_volume(value)

        # Multiple rapid calls only execute once after 100ms
        update_volume(50)
        update_volume(55)
        update_volume(60)  # Only this one executes
    """
    def decorator(func: Callable) -> Callable:
        debouncer = Debouncer(delay_ms=delay_ms)

        @wraps(func)
        def wrapper(*args, **kwargs):
            debouncer.call(func, *args, **kwargs)

        # Expose debouncer for manual control
        wrapper.debouncer = debouncer
        wrapper.cancel = debouncer.cancel
        wrapper.flush = debouncer.flush

        return wrapper

    return decorator


class ThrottledDebouncer:
    """
    Combines throttling and debouncing.
    Executes immediately on first call, then debounces subsequent calls.

    Good for sliders where you want immediate feedback but don't want
    to spam the backend with every tiny change.
    """

    def __init__(self, delay_ms: int = 50, throttle_ms: int = 100):
        """
        Initialize throttled debouncer.

        Args:
            delay_ms: Debounce delay in milliseconds
            throttle_ms: Minimum time between immediate executions
        """
        self.delay_ms = delay_ms
        self.throttle_ms = throttle_ms
        self._timeout_id: Optional[int] = None
        self._last_execution: int = 0
        self._pending_func: Optional[Callable] = None
        self._pending_args: tuple = ()
        self._pending_kwargs: dict = {}

    def call(self, func: Callable, *args, **kwargs) -> None:
        """
        Schedule a throttled/debounced function call.
        """
        current_time = GLib.get_monotonic_time() // 1000  # ms

        # Cancel any pending debounced call
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

        # Check if we should execute immediately (throttle)
        if current_time - self._last_execution >= self.throttle_ms:
            # Execute immediately
            self._last_execution = current_time
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Throttled call failed: {e}")
        else:
            # Debounce: schedule for later
            self._pending_func = func
            self._pending_args = args
            self._pending_kwargs = kwargs
            self._timeout_id = GLib.timeout_add(self.delay_ms, self._execute)

    def _execute(self) -> bool:
        """Execute the pending function call"""
        self._timeout_id = None
        self._last_execution = GLib.get_monotonic_time() // 1000

        if self._pending_func:
            try:
                self._pending_func(*self._pending_args, **self._pending_kwargs)
            except Exception as e:
                print(f"Debounced call failed: {e}")
            finally:
                self._pending_func = None
                self._pending_args = ()
                self._pending_kwargs = {}

        return False


class DebouncedScale:
    """
    Mixin for Scale widgets that debounces value-changed signals.

    Usage:
        class VolumeSlider(Scale, DebouncedScale):
            def __init__(self):
                Scale.__init__(self, ...)
                DebouncedScale.__init__(self, delay_ms=50)
                self.connect("value-changed", self.on_value_changed_debounced)

            def on_actual_value_changed(self, value):
                # This is called after debouncing
                set_volume(value)
    """

    def __init__(self, delay_ms: int = 50):
        self._scale_debouncer = Debouncer(delay_ms=delay_ms)
        self._updating_from_external = False

    def on_value_changed_debounced(self, scale):
        """Connect this to 'value-changed' signal"""
        if self._updating_from_external:
            return

        value = scale.get_value()
        self._scale_debouncer.call(self.on_actual_value_changed, value)

    def on_actual_value_changed(self, value):
        """Override this in subclass to handle debounced value changes"""
        pass

    def set_value_external(self, value):
        """Set value from external source (won't trigger debounced callback)"""
        self._updating_from_external = True
        try:
            self.set_value(value)
        finally:
            self._updating_from_external = False
