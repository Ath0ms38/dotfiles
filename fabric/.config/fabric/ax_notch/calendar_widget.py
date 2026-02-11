"""
Calendar Widget - Modern calendar display with navigation
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from gi.repository import Gtk, GLib, Pango
import datetime
import calendar

from . import icons


class CalendarDay(Button):
    """Single day button in the calendar grid"""

    def __init__(self, day: int, is_current_month: bool = True, is_today: bool = False, **kwargs):
        super().__init__(
            name="ax-calendar-day",
            **kwargs,
        )

        self.day = day
        self.is_current_month = is_current_month
        self.is_today = is_today

        label = Label(label=str(day) if day > 0 else "")
        self.add(label)

        # Apply styles
        if is_today:
            self.add_style_class("today")
        if not is_current_month:
            self.add_style_class("other-month")


class Calendar(Box):
    """Modern calendar widget with navigation and better styling"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-calendar",
            orientation="v",
            spacing=8,
            h_expand=True,
            **kwargs,
        )

        self.current_date = datetime.date.today()
        self.view_year = self.current_date.year
        self.view_month = self.current_date.month

        # Build UI
        self._build_header()
        self._build_weekday_row()
        self._build_calendar_grid()

        # Update time display periodically
        GLib.timeout_add_seconds(60, self._update_time_display)

    def _build_header(self):
        """Build the header with date, time, and navigation"""
        # Top row: Date and Time
        top_row = Box(
            name="ax-calendar-top",
            orientation="h",
            h_expand=True,
        )

        # Date display (left)
        self.date_label = Label(
            name="ax-calendar-date",
            h_align="start",
        )

        # Time display (right)
        self.time_label = Label(
            name="ax-calendar-time",
            h_align="end",
            h_expand=True,
        )

        self._update_time_display()

        top_row.add(self.date_label)
        top_row.add(self.time_label)

        # Navigation row: < Month Year >
        nav_row = Box(
            name="ax-calendar-nav",
            orientation="h",
            h_expand=True,
            h_align="center",
            spacing=12,
        )

        # Previous month button
        prev_btn = Button(name="ax-calendar-prev")
        prev_btn.add(Label(label="󰅁"))
        prev_btn.connect("clicked", self._prev_month)

        # Month/Year label
        self.month_label = Label(
            name="ax-calendar-month",
            h_expand=True,
            h_align="center",
        )

        # Next month button
        next_btn = Button(name="ax-calendar-next")
        next_btn.add(Label(label="󰅂"))
        next_btn.connect("clicked", self._next_month)

        # Today button
        today_btn = Button(name="ax-calendar-today")
        today_btn.add(Label(label=icons.calendar))
        today_btn.set_tooltip_text("Go to today")
        today_btn.connect("clicked", self._go_today)

        nav_row.add(prev_btn)
        nav_row.add(self.month_label)
        nav_row.add(next_btn)
        nav_row.add(today_btn)

        self.add(top_row)
        self.add(nav_row)

    def _build_weekday_row(self):
        """Build the weekday header row"""
        weekday_row = Box(
            name="ax-calendar-weekdays",
            orientation="h",
            h_expand=True,
            homogeneous=True,
        )

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for day in weekdays:
            label = Label(
                name="ax-calendar-weekday",
                label=day,
            )
            weekday_row.add(label)

        self.add(weekday_row)

    def _build_calendar_grid(self):
        """Build the calendar day grid"""
        self.grid_container = Box(
            name="ax-calendar-grid-container",
            orientation="v",
            spacing=2,
            h_expand=True,
        )

        self.add(self.grid_container)
        self._update_calendar()

    def _update_calendar(self):
        """Update the calendar grid for current view month"""
        # Clear existing grid
        for child in self.grid_container.get_children():
            self.grid_container.remove(child)

        # Update month label
        month_name = calendar.month_name[self.view_month]
        self.month_label.set_label(f"{month_name} {self.view_year}")

        # Get calendar data
        cal = calendar.Calendar(firstweekday=0)  # Monday first
        month_days = cal.monthdayscalendar(self.view_year, self.view_month)

        today = datetime.date.today()

        # Build grid rows
        for week in month_days:
            row = Box(
                name="ax-calendar-week",
                orientation="h",
                h_expand=True,
                homogeneous=True,
            )

            for day in week:
                is_today = (
                    day == today.day and
                    self.view_month == today.month and
                    self.view_year == today.year
                )

                day_btn = CalendarDay(
                    day=day,
                    is_current_month=(day != 0),
                    is_today=is_today,
                )

                if day != 0:
                    day_btn.connect("clicked", self._on_day_clicked, day)

                row.add(day_btn)

            self.grid_container.add(row)

        self.grid_container.show_all()

    def _update_time_display(self):
        """Update the date and time labels"""
        now = datetime.datetime.now()
        self.date_label.set_label(now.strftime("%A, %B %d"))
        self.time_label.set_label(now.strftime("%H:%M"))
        return True

    def _prev_month(self, btn):
        """Go to previous month"""
        if self.view_month == 1:
            self.view_month = 12
            self.view_year -= 1
        else:
            self.view_month -= 1
        self._update_calendar()

    def _next_month(self, btn):
        """Go to next month"""
        if self.view_month == 12:
            self.view_month = 1
            self.view_year += 1
        else:
            self.view_month += 1
        self._update_calendar()

    def _go_today(self, btn):
        """Go to current month"""
        today = datetime.date.today()
        self.view_year = today.year
        self.view_month = today.month
        self._update_calendar()

    def _on_day_clicked(self, btn, day):
        """Handle day click - could be extended for events"""
        pass  # Placeholder for future event functionality
