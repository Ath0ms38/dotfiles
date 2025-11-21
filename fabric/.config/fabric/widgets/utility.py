"""
Utility Widget
Clock alarms, note taking, and reminders
"""

import os
import json
import time
from datetime import datetime
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.wayland import WaylandWindow


class UtilityWidget(WaylandWindow):
    """Utility popup widget for clock, notes, and reminders"""

    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="top right",
            margin="50px 20px 0px 0px",
            keyboard_mode="on-demand",
            name="utility-widget",
            visible=False,
            **kwargs
        )

        # Data file paths
        self.config_dir = os.path.expanduser("~/.config/fabric")
        self.notes_file = os.path.join(self.config_dir, "notes.json")
        self.reminders_file = os.path.join(self.config_dir, "reminders.json")

        # Load data
        self.notes = self.load_notes()
        self.reminders = self.load_reminders()

        # Build widget
        self.children = self.build_content()

    def load_notes(self):
        """Load notes from file"""
        try:
            if os.path.exists(self.notes_file):
                with open(self.notes_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading notes: {e}")
        return []

    def save_notes(self):
        """Save notes to file"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.notes_file, 'w') as f:
                json.dump(self.notes, f, indent=2)
        except Exception as e:
            print(f"Error saving notes: {e}")

    def load_reminders(self):
        """Load reminders from file"""
        try:
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading reminders: {e}")
        return []

    def save_reminders(self):
        """Save reminders to file"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.reminders_file, 'w') as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            print(f"Error saving reminders: {e}")

    def add_note(self, text: str):
        """Add a new note"""
        if text.strip():
            note = {
                "text": text.strip(),
                "timestamp": datetime.now().isoformat(),
            }
            self.notes.insert(0, note)
            self.save_notes()
            self.rebuild_content()

    def delete_note(self, index: int):
        """Delete a note"""
        if 0 <= index < len(self.notes):
            self.notes.pop(index)
            self.save_notes()
            self.rebuild_content()

    def add_reminder(self, text: str):
        """Add a new reminder"""
        if text.strip():
            reminder = {
                "text": text.strip(),
                "timestamp": datetime.now().isoformat(),
                "completed": False,
            }
            self.reminders.insert(0, reminder)
            self.save_reminders()
            self.rebuild_content()

    def toggle_reminder(self, index: int):
        """Toggle reminder completion"""
        if 0 <= index < len(self.reminders):
            self.reminders[index]["completed"] = not self.reminders[index]["completed"]
            self.save_reminders()
            self.rebuild_content()

    def delete_reminder(self, index: int):
        """Delete a reminder"""
        if 0 <= index < len(self.reminders):
            self.reminders.pop(index)
            self.save_reminders()
            self.rebuild_content()

    def build_clock_section(self):
        """Build clock display section"""
        now = datetime.now()

        return Box(
            orientation="v",
            spacing=8,
            name="clock-section",
            children=[
                Label(
                    label=now.strftime("%I:%M:%S %p"),
                    name="clock-time",
                    style="font-size: 32px; font-weight: bold;"
                ),
                Label(
                    label=now.strftime("%A, %B %d, %Y"),
                    name="clock-date",
                    style="font-size: 14px; opacity: 0.9;"
                ),
                Label(
                    label=f"Week {now.strftime('%W')}",
                    name="clock-week",
                    style="font-size: 12px; opacity: 0.7;"
                ),
            ]
        )

    def build_notes_section(self):
        """Build notes section"""
        # Note entry
        note_entry = Entry(
            placeholder_text="Enter a new note...",
            name="note-entry",
            h_expand=True
        )

        add_note_btn = Button(
            label="Add",
            on_clicked=lambda *_: (
                self.add_note(note_entry.get_text()),
                note_entry.set_text("")
            )
        )

        # Note input box
        note_input = Box(
            orientation="h",
            spacing=8,
            children=[note_entry, add_note_btn]
        )

        # Notes list
        notes_list = []
        for i, note in enumerate(self.notes[:10]):  # Limit to 10 notes
            timestamp = datetime.fromisoformat(note["timestamp"])
            time_str = timestamp.strftime("%m/%d %H:%M")

            note_item = Box(
                orientation="h",
                spacing=8,
                name="note-item",
                children=[
                    Label(
                        label=f"📝 {note['text']}",
                        h_expand=True,
                        h_align="start",
                        style="font-size: 12px;"
                    ),
                    Label(
                        label=time_str,
                        style="font-size: 10px; opacity: 0.6;"
                    ),
                    Button(
                        label="✕",
                        on_clicked=lambda *_, idx=i: self.delete_note(idx),
                        style="min-width: 20px; padding: 2px 6px;"
                    ),
                ]
            )
            notes_list.append(note_item)

        if not notes_list:
            notes_list = [
                Label(
                    label="No notes yet",
                    name="empty-message",
                    style="opacity: 0.7; font-style: italic; padding: 8px;"
                )
            ]

        return Box(
            orientation="v",
            spacing=8,
            name="notes-section",
            children=[
                Label(
                    label="📝 Notes",
                    name="section-title",
                    style="font-size: 14px; font-weight: bold; margin-top: 16px;"
                ),
                note_input,
                Box(
                    orientation="v",
                    spacing=4,
                    children=notes_list
                ),
            ]
        )

    def build_reminders_section(self):
        """Build reminders section"""
        # Reminder entry
        reminder_entry = Entry(
            placeholder_text="Enter a new reminder...",
            name="reminder-entry",
            h_expand=True
        )

        add_reminder_btn = Button(
            label="Add",
            on_clicked=lambda *_: (
                self.add_reminder(reminder_entry.get_text()),
                reminder_entry.set_text("")
            )
        )

        # Reminder input box
        reminder_input = Box(
            orientation="h",
            spacing=8,
            children=[reminder_entry, add_reminder_btn]
        )

        # Reminders list
        reminders_list = []
        for i, reminder in enumerate(self.reminders[:10]):  # Limit to 10 reminders
            completed = reminder["completed"]
            checkbox = "☑" if completed else "☐"
            text_style = "text-decoration: line-through; opacity: 0.6;" if completed else ""

            reminder_item = Box(
                orientation="h",
                spacing=8,
                name="reminder-item",
                children=[
                    Button(
                        label=checkbox,
                        on_clicked=lambda *_, idx=i: self.toggle_reminder(idx),
                        style="min-width: 30px; padding: 2px 6px;"
                    ),
                    Label(
                        label=reminder['text'],
                        h_expand=True,
                        h_align="start",
                        style=f"font-size: 12px; {text_style}"
                    ),
                    Button(
                        label="✕",
                        on_clicked=lambda *_, idx=i: self.delete_reminder(idx),
                        style="min-width: 20px; padding: 2px 6px;"
                    ),
                ]
            )
            reminders_list.append(reminder_item)

        if not reminders_list:
            reminders_list = [
                Label(
                    label="No reminders yet",
                    name="empty-message",
                    style="opacity: 0.7; font-style: italic; padding: 8px;"
                )
            ]

        return Box(
            orientation="v",
            spacing=8,
            name="reminders-section",
            children=[
                Label(
                    label="✓ Reminders",
                    name="section-title",
                    style="font-size: 14px; font-weight: bold; margin-top: 16px;"
                ),
                reminder_input,
                Box(
                    orientation="v",
                    spacing=4,
                    children=reminders_list
                ),
            ]
        )

    def build_content(self):
        """Build the widget content"""
        content = Box(
            orientation="v",
            spacing=16,
            name="utility-content",
            children=[
                Label(
                    label=" Utilities",
                    name="utility-title",
                    style="font-size: 16px; font-weight: bold;"
                ),
                self.build_clock_section(),
                self.build_notes_section(),
                self.build_reminders_section(),
            ]
        )

        return ScrolledWindow(
            min_content_size=(450, 200),
            max_content_size=(450, 700),
            child=content,
            style="padding: 16px;"
        )

    def rebuild_content(self):
        """Rebuild the widget content"""
        self.children = self.build_content()

    def toggle(self):
        """Toggle widget visibility"""
        if self.get_visible():
            self.hide()
        else:
            self.rebuild_content()  # Refresh when opening
            self.show_all()


# Create singleton instance
utility_widget = None


def get_utility_widget():
    """Get or create the utility widget singleton"""
    global utility_widget
    if utility_widget is None:
        utility_widget = UtilityWidget()
    return utility_widget
