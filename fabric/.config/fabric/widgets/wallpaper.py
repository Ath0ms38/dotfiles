"""
Wallpaper Selection Widget
Matugen-integrated wallpaper selector with:
- Thumbnail grid of available wallpapers
- Color scheme selection dropdown
- Matugen toggle switch
- Random wallpaper button
"""

import os
import hashlib
import random
from concurrent.futures import ThreadPoolExecutor
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.utils.helpers import exec_shell_command_async
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk
from .base_popup import BasePopup

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[WALLPAPER] PIL not available, thumbnails will be generated with GdkPixbuf")


class WallpaperWidget(BasePopup):
    """Wallpaper selector popup with Matugen integration"""

    # Configuration
    WALLPAPERS_DIR = os.path.expanduser("~/dotfiles/wallpapers")
    CACHE_DIR = os.path.expanduser("~/.cache/fabric/wallpaper-thumbs")
    THUMBNAIL_SIZE = 120
    MATUGEN_STATE_FILE = os.path.expanduser("~/.config/fabric/matugen_enabled")
    CURRENT_WALL_SYMLINK = os.path.expanduser("~/.current.wall")

    # Color schemes available in Matugen
    SCHEMES = [
        ("scheme-tonal-spot", "Tonal Spot"),
        ("scheme-content", "Content"),
        ("scheme-expressive", "Expressive"),
        ("scheme-fidelity", "Fidelity"),
        ("scheme-fruit-salad", "Fruit Salad"),
        ("scheme-monochrome", "Monochrome"),
        ("scheme-neutral", "Neutral"),
        ("scheme-rainbow", "Rainbow"),
    ]

    def __init__(self, **kwargs):
        self.files = []
        self.thumbnails = {}  # Cache: filename -> pixbuf
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.matugen_enabled = self._load_matugen_state()
        self.selected_scheme = "scheme-tonal-spot"

        super().__init__(
            name="wallpaper-widget",
            anchor="top right",
            margin="50px 20px 0px 0px",
            width=500,
            **kwargs
        )

        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _load_matugen_state(self):
        """Load Matugen enabled state from file"""
        try:
            if os.path.exists(self.MATUGEN_STATE_FILE):
                with open(self.MATUGEN_STATE_FILE, 'r') as f:
                    return f.read().strip().lower() == 'true'
        except Exception:
            pass
        return True  # Default enabled

    def _save_matugen_state(self, enabled):
        """Save Matugen enabled state to file"""
        try:
            os.makedirs(os.path.dirname(self.MATUGEN_STATE_FILE), exist_ok=True)
            with open(self.MATUGEN_STATE_FILE, 'w') as f:
                f.write(str(enabled).lower())
        except Exception as e:
            print(f"[WALLPAPER] Error saving matugen state: {e}")

    def build_content(self):
        """Build the wallpaper widget content"""
        # Header with title
        title = Label(
            label="󰸉  Wallpapers",
            name="wallpaper-title",
        )

        # Scheme dropdown
        self.scheme_combo = Gtk.ComboBoxText()
        self.scheme_combo.set_name("scheme-dropdown")
        for scheme_id, scheme_name in self.SCHEMES:
            self.scheme_combo.append(scheme_id, scheme_name)
        self.scheme_combo.set_active_id("scheme-tonal-spot")
        self.scheme_combo.connect("changed", self._on_scheme_changed)

        # Matugen toggle
        matugen_label = Label(label="Matugen")
        self.matugen_switch = Gtk.Switch()
        self.matugen_switch.set_active(self.matugen_enabled)
        self.matugen_switch.connect("notify::active", self._on_matugen_toggled)

        matugen_box = Box(
            orientation="h",
            spacing=8,
            children=[matugen_label, self.matugen_switch]
        )

        # Random button
        random_button = Button(
            label="🎲 Random",
            name="random-wallpaper-btn",
            on_clicked=self._set_random_wallpaper
        )

        # Controls row
        controls = Box(
            orientation="h",
            spacing=12,
            name="wallpaper-controls",
            children=[
                self.scheme_combo,
                matugen_box,
                random_button,
            ]
        )

        # Wallpaper grid container
        self.grid = Gtk.FlowBox()
        self.grid.set_valign(Gtk.Align.START)
        self.grid.set_max_children_per_line(4)
        self.grid.set_min_children_per_line(3)
        self.grid.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.grid.set_homogeneous(True)
        self.grid.set_row_spacing(8)
        self.grid.set_column_spacing(8)
        self.grid.connect("child-activated", self._on_wallpaper_selected)

        # Scrolled window for grid
        scroll = ScrolledWindow(
            name="wallpaper-scroll",
            min_content_size=(460, 200),
            max_content_size=(460, 350),
            child=self.grid,
        )

        return Box(
            orientation="v",
            spacing=12,
            name="wallpaper-content",
            children=[
                title,
                controls,
                scroll,
            ]
        )

    def on_open(self):
        """Called when widget opens - load wallpapers"""
        self._load_wallpapers()

    def _load_wallpapers(self):
        """Load wallpaper files and generate thumbnails"""
        self.files = []

        # Clear existing grid
        for child in self.grid.get_children():
            self.grid.remove(child)

        if not os.path.isdir(self.WALLPAPERS_DIR):
            print(f"[WALLPAPER] Directory not found: {self.WALLPAPERS_DIR}")
            return

        # Get list of image files
        for f in os.listdir(self.WALLPAPERS_DIR):
            if self._is_image(f):
                self.files.append(f)

        self.files.sort()
        print(f"[WALLPAPER] Found {len(self.files)} wallpapers")

        # Add thumbnails to grid
        for filename in self.files:
            self._add_wallpaper_item(filename)

        self.grid.show_all()

    def _add_wallpaper_item(self, filename):
        """Add a wallpaper thumbnail to the grid"""
        full_path = os.path.join(self.WALLPAPERS_DIR, filename)
        cache_path = self._get_cache_path(filename)

        # Create thumbnail container
        item_box = Box(
            orientation="v",
            spacing=4,
            name="wallpaper-item",
        )

        # Create image widget
        image = Gtk.Image()
        image.set_size_request(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE)

        # Try to load from cache or generate
        if os.path.exists(cache_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    cache_path, self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE, True
                )
                image.set_from_pixbuf(pixbuf)
            except Exception as e:
                print(f"[WALLPAPER] Error loading cached thumbnail: {e}")
                image.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        else:
            # Generate thumbnail in background
            self.executor.submit(self._generate_thumbnail, filename, image)
            image.set_from_icon_name("image-loading", Gtk.IconSize.DIALOG)

        # Store filename as data
        item_box.filename = filename

        item_box.add(image)

        # Add truncated filename label
        name_label = Label(label=filename[:15] + "..." if len(filename) > 15 else filename)
        name_label.set_line_wrap(True)
        name_label.set_max_width_chars(12)
        item_box.add(name_label)

        self.grid.add(item_box)

    def _generate_thumbnail(self, filename, image_widget):
        """Generate thumbnail in background thread"""
        full_path = os.path.join(self.WALLPAPERS_DIR, filename)
        cache_path = self._get_cache_path(filename)

        try:
            if HAS_PIL:
                # Use PIL for better quality thumbnails
                with Image.open(full_path) as img:
                    # Crop to square from center
                    size = min(img.size)
                    left = (img.width - size) // 2
                    top = (img.height - size) // 2
                    img = img.crop((left, top, left + size, top + size))
                    img.thumbnail((self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
                    img.save(cache_path, "PNG")
            else:
                # Use GdkPixbuf
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    full_path, self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE, True
                )
                pixbuf.savev(cache_path, "png", [], [])

            # Update widget on main thread
            GLib.idle_add(self._update_thumbnail_widget, image_widget, cache_path)

        except Exception as e:
            print(f"[WALLPAPER] Error generating thumbnail for {filename}: {e}")

    def _update_thumbnail_widget(self, image_widget, cache_path):
        """Update thumbnail widget on main thread"""
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                cache_path, self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE, True
            )
            image_widget.set_from_pixbuf(pixbuf)
        except Exception as e:
            print(f"[WALLPAPER] Error updating thumbnail: {e}")
        return False

    def _on_wallpaper_selected(self, flowbox, child):
        """Handle wallpaper selection"""
        item_box = child.get_child()
        if not hasattr(item_box, 'filename'):
            return

        filename = item_box.filename
        full_path = os.path.join(self.WALLPAPERS_DIR, filename)

        print(f"[WALLPAPER] Selected: {filename}")
        self._apply_wallpaper(full_path)

    def _apply_wallpaper(self, full_path):
        """Apply wallpaper and optionally run Matugen"""
        # Update current wallpaper symlink
        try:
            if os.path.lexists(self.CURRENT_WALL_SYMLINK):
                os.remove(self.CURRENT_WALL_SYMLINK)
            os.symlink(full_path, self.CURRENT_WALL_SYMLINK)
            print(f"[WALLPAPER] Updated symlink: {self.CURRENT_WALL_SYMLINK} -> {full_path}")
        except Exception as e:
            print(f"[WALLPAPER] Error updating symlink: {e}")

        # Apply wallpaper
        if self.matugen_enabled:
            scheme = self.scheme_combo.get_active_id() or "scheme-tonal-spot"
            cmd = f'matugen image "{full_path}" -t {scheme}'
            print(f"[WALLPAPER] Running: {cmd}")
            exec_shell_command_async(cmd)
        else:
            # Direct wallpaper set via hyprctl
            cmd = f'hyprctl hyprpaper wallpaper ",{full_path}"'
            print(f"[WALLPAPER] Running: {cmd}")
            exec_shell_command_async(cmd)

        # Close the popup after selection
        self.close()

    def _set_random_wallpaper(self, *args):
        """Set a random wallpaper"""
        if not self.files:
            print("[WALLPAPER] No wallpapers available")
            return

        filename = random.choice(self.files)
        full_path = os.path.join(self.WALLPAPERS_DIR, filename)

        print(f"[WALLPAPER] Random selection: {filename}")
        self._apply_wallpaper(full_path)

    def _on_scheme_changed(self, combo):
        """Handle scheme selection change"""
        self.selected_scheme = combo.get_active_id()
        print(f"[WALLPAPER] Scheme changed to: {self.selected_scheme}")

    def _on_matugen_toggled(self, switch, gparam):
        """Handle Matugen toggle"""
        self.matugen_enabled = switch.get_active()
        self._save_matugen_state(self.matugen_enabled)
        print(f"[WALLPAPER] Matugen {'enabled' if self.matugen_enabled else 'disabled'}")

    def _get_cache_path(self, filename):
        """Get cache path for thumbnail"""
        file_hash = hashlib.md5(filename.encode()).hexdigest()
        return os.path.join(self.CACHE_DIR, f"{file_hash}.png")

    @staticmethod
    def _is_image(filename):
        """Check if file is an image"""
        return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'))


# Singleton instance
_wallpaper_widget = None


def get_wallpaper_widget():
    """Get or create the wallpaper widget singleton"""
    global _wallpaper_widget
    if _wallpaper_widget is None:
        _wallpaper_widget = WallpaperWidget()
    return _wallpaper_widget
