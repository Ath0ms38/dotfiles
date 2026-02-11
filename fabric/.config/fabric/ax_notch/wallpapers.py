"""
Wallpaper Selector with Matugen Integration
Browse wallpapers and apply with color scheme generation
"""

import os
import random
import hashlib
import shutil
from concurrent.futures import ThreadPoolExecutor

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.utils.helpers import exec_shell_command_async
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk

from . import icons

# Try to import PIL for thumbnail generation
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("PIL not available, thumbnails may not work")


# Default wallpapers directory
DEFAULT_WALLPAPERS_DIR = os.path.expanduser("~/Pictures/Wallpapers")
CACHE_DIR = os.path.expanduser("~/.cache/fabric-bar/thumbs")


class WallpaperSelector(Box):
    """Wallpaper browser with matugen integration"""

    def __init__(self, notch=None, **kwargs):
        super().__init__(
            name="ax-wallpapers",
            orientation="v",
            spacing=8,
            h_expand=True,
            v_expand=True,
            h_align="fill",
            v_align="fill",
            visible=True,
            all_visible=True,
            **kwargs,
        )

        self.notch = notch
        self.files = []
        self.thumbnails = []
        self.thumbnail_queue = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.selected_index = -1

        # Ensure cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)

        # Get wallpapers directory from config or use default
        self.wallpapers_dir = self._get_wallpapers_dir()

        # Color schemes for matugen
        self.schemes = {
            "scheme-tonal-spot": "Tonal Spot",
            "scheme-content": "Content",
            "scheme-expressive": "Expressive",
            "scheme-fidelity": "Fidelity",
            "scheme-fruit-salad": "Fruit Salad",
            "scheme-monochrome": "Monochrome",
            "scheme-neutral": "Neutral",
            "scheme-rainbow": "Rainbow",
        }

        # Matugen toggle state
        self.matugen_enabled = True

        # Build UI
        self._build_ui()

        # Load wallpapers
        GLib.idle_add(self._load_wallpapers)

        # Setup file monitor
        self._setup_file_monitor()

    def _get_wallpapers_dir(self) -> str:
        """Get wallpapers directory from config or use default"""
        # Try to load from config
        try:
            from services.config import get_config
            config = get_config()
            if hasattr(config, 'wallpapers_dir') and config.wallpapers_dir:
                return os.path.expanduser(config.wallpapers_dir)
        except Exception:
            pass

        # Use default
        if os.path.exists(DEFAULT_WALLPAPERS_DIR):
            return DEFAULT_WALLPAPERS_DIR

        # Fallback to home Pictures
        return os.path.expanduser("~/Pictures")

    def _build_ui(self):
        """Build the wallpaper selector UI"""

        # Icon view for wallpapers (create first so callbacks work)
        self.icon_view = Gtk.IconView(name="ax-wall-icons")
        self.icon_view.set_model(Gtk.ListStore(GdkPixbuf.Pixbuf, str))
        self.icon_view.set_pixbuf_column(0)
        self.icon_view.set_text_column(-1)  # Hide text
        self.icon_view.set_item_width(0)
        self.icon_view.set_visible(True)
        self.icon_view.connect("item-activated", self._on_wallpaper_selected)

        # Header with search and controls
        self.search_entry = Entry(
            name="ax-wall-search",
            placeholder="Search Wallpapers...",
            h_expand=True,
            notify_text=lambda entry, *_: self._filter_wallpapers(entry.get_text()),
        )
        self.search_entry.connect("key-press-event", self._on_search_key_press)

        # Scheme dropdown
        self.scheme_dropdown = Gtk.ComboBoxText(name="ax-scheme-dropdown")
        self.scheme_dropdown.set_tooltip_text("Color scheme")
        for key, name in self.schemes.items():
            self.scheme_dropdown.append(key, name)
        self.scheme_dropdown.set_active_id("scheme-tonal-spot")

        # Matugen toggle
        self.matugen_switch = Gtk.Switch(name="ax-matugen-switch")
        self.matugen_switch.set_active(True)
        self.matugen_switch.set_tooltip_text("Enable Matugen colors")
        self.matugen_switch.connect("notify::active", self._on_matugen_toggled)

        # Random wallpaper button
        self.random_btn = Button(
            name="ax-wall-random",
            child=Label(label=icons.dice_1),
            tooltip_text="Random wallpaper",
            on_clicked=lambda *_: self._set_random_wallpaper(),
        )

        # Header box
        header = Box(
            name="ax-wall-header",
            orientation="h",
            spacing=8,
            children=[
                self.random_btn,
                self.search_entry,
                self.scheme_dropdown,
                self.matugen_switch,
            ],
        )

        # Scrolled window for icon view
        self.scrolled = ScrolledWindow(
            name="ax-wall-scrolled",
            h_expand=True,
            v_expand=True,
            h_align="fill",
            v_align="fill",
            child=self.icon_view,
            propagate_width=False,
            propagate_height=False,
        )

        self.pack_start(header, False, False, 0)
        self.pack_start(self.scrolled, True, True, 0)

        self.show_all()

    def _load_wallpapers(self):
        """Load wallpapers from directory"""
        if not os.path.exists(self.wallpapers_dir):
            print(f"Wallpapers directory not found: {self.wallpapers_dir}")
            return False

        self.files = []
        for filename in os.listdir(self.wallpapers_dir):
            if self._is_image(filename):
                self.files.append(filename)

        self.files.sort()

        # Start thumbnail generation
        self._start_thumbnail_thread()

        return False

    def _start_thumbnail_thread(self):
        """Start background thread to generate thumbnails"""
        GLib.Thread.new("thumb-loader", self._generate_thumbnails, None)

    def _generate_thumbnails(self, _data):
        """Generate thumbnails for all wallpapers"""
        for filename in self.files:
            self.executor.submit(self._process_file, filename)

    def _process_file(self, filename: str):
        """Process a single wallpaper file"""
        full_path = os.path.join(self.wallpapers_dir, filename)
        cache_path = self._get_cache_path(filename)

        # Generate thumbnail if not cached
        if not os.path.exists(cache_path) and HAS_PIL:
            try:
                with Image.open(full_path) as img:
                    # Crop to square
                    size = min(img.size)
                    left = (img.width - size) // 2
                    top = (img.height - size) // 2
                    img_cropped = img.crop((left, top, left + size, top + size))
                    img_cropped.thumbnail((96, 96), Image.Resampling.LANCZOS)
                    img_cropped.save(cache_path, "PNG")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                return

        # Queue for UI update
        self.thumbnail_queue.append((cache_path, filename))
        GLib.idle_add(self._process_thumbnail_batch)

    def _process_thumbnail_batch(self):
        """Process batch of thumbnails on main thread"""
        batch = self.thumbnail_queue[:10]
        del self.thumbnail_queue[:10]

        model = self.icon_view.get_model()

        for cache_path, filename in batch:
            if os.path.exists(cache_path):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(cache_path)
                    self.thumbnails.append((pixbuf, filename))
                    model.append([pixbuf, filename])
                except Exception as e:
                    print(f"Error loading thumbnail {cache_path}: {e}")

        if self.thumbnail_queue:
            GLib.idle_add(self._process_thumbnail_batch)

        return False

    def _get_cache_path(self, filename: str) -> str:
        """Get cache path for a wallpaper thumbnail"""
        file_hash = hashlib.md5(filename.encode()).hexdigest()
        return os.path.join(CACHE_DIR, f"{file_hash}.png")

    @staticmethod
    def _is_image(filename: str) -> bool:
        """Check if file is an image"""
        return filename.lower().endswith(
            (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
        )

    def _filter_wallpapers(self, query: str):
        """Filter wallpapers by search query"""
        model = self.icon_view.get_model()
        model.clear()

        filtered = [
            (thumb, name)
            for thumb, name in self.thumbnails
            if query.lower() in name.lower()
        ]
        filtered.sort(key=lambda x: x[1].lower())

        for pixbuf, filename in filtered:
            model.append([pixbuf, filename])

    def _on_wallpaper_selected(self, iconview, path):
        """Handle wallpaper selection"""
        model = iconview.get_model()
        filename = model[path][1]
        self._apply_wallpaper(filename)

    def _apply_wallpaper(self, filename: str):
        """Apply selected wallpaper"""
        full_path = os.path.join(self.wallpapers_dir, filename)
        scheme = self.scheme_dropdown.get_active_id()

        # Update current wall symlink
        current_wall = os.path.expanduser("~/.current.wall")
        if os.path.exists(current_wall):
            os.remove(current_wall)
        os.symlink(full_path, current_wall)

        # Apply with matugen or just set wallpaper
        if self.matugen_enabled:
            exec_shell_command_async(f'matugen image "{full_path}" -t {scheme}')
        else:
            # Use swww or similar for wallpaper without matugen
            exec_shell_command_async(
                f'swww img "{full_path}" -t outer --transition-duration 1.5'
            )

        print(f"Applied wallpaper: {filename}")

    def _set_random_wallpaper(self):
        """Set a random wallpaper"""
        if not self.files:
            return

        filename = random.choice(self.files)
        self._apply_wallpaper(filename)

        # Randomize dice icon
        dice_icons = [icons.dice_1, icons.dice_2, icons.dice_3,
                      icons.dice_4, icons.dice_5, icons.dice_6]
        self.random_btn.get_child().set_label(random.choice(dice_icons))

    def _on_matugen_toggled(self, switch, _param):
        """Handle matugen toggle"""
        self.matugen_enabled = switch.get_active()

    def _on_search_key_press(self, widget, event):
        """Handle key press in search"""
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            # Apply first matching wallpaper
            model = self.icon_view.get_model()
            if len(model) > 0:
                self._on_wallpaper_selected(
                    self.icon_view,
                    Gtk.TreePath.new_from_indices([0])
                )
            return True
        return False

    def _setup_file_monitor(self):
        """Monitor wallpapers directory for changes"""
        if not os.path.exists(self.wallpapers_dir):
            return

        gfile = Gio.File.new_for_path(self.wallpapers_dir)
        self.file_monitor = gfile.monitor_directory(Gio.FileMonitorFlags.NONE, None)
        self.file_monitor.connect("changed", self._on_directory_changed)

    def _on_directory_changed(self, monitor, file, other_file, event_type):
        """Handle wallpaper directory changes"""
        filename = file.get_basename()

        if event_type == Gio.FileMonitorEvent.CREATED:
            if self._is_image(filename) and filename not in self.files:
                self.files.append(filename)
                self.files.sort()
                self.executor.submit(self._process_file, filename)

        elif event_type == Gio.FileMonitorEvent.DELETED:
            if filename in self.files:
                self.files.remove(filename)
                # Remove from thumbnails
                self.thumbnails = [(p, n) for p, n in self.thumbnails if n != filename]
                # Refresh view
                self._filter_wallpapers(self.search_entry.get_text())
