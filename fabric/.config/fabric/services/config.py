"""
Configuration Service
Centralized configuration management for the Fabric bar.
Loads settings from ~/.config/fabric/config.json with sensible defaults.

Usage:
    from services.config import config, get_config

    # Access config values
    bar_position = config.bar_position

    # Check widget visibility
    if config.widgets_visible["audio"]:
        # show audio button

    # Get animation settings
    duration = config.animation_duration
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from fabric.core.service import Service, Signal, Property


# Default configuration values
DEFAULTS = {
    # Bar positioning
    "bar_position": "top",  # "top", "bottom", "left", "right"
    "bar_margin": 4,
    "bar_monitor": 0,  # Which monitor(s) to show bar on (-1 = all)

    # Widget visibility
    "widgets_visible": {
        "wallpaper": True,
        "audio": True,
        "network": True,
        "battery": True,
        "system_tray": True,
        "utility": True,
        "power_menu": True,
    },

    # Special workspaces
    "special_workspaces": {
        "discord": {
            "enabled": True,
            "workspace": 11,
            "icon": "󰙯",
            "command": "discord",
            "class": "discord",
            "color": "#5865f2",
        },
        "vscode": {
            "enabled": True,
            "workspace": 12,
            "icon": "󰨞",
            "command": "code",
            "class": "Code",
            "color": "#ff9f43",
        },
        "minecraft": {
            "enabled": True,
            "workspace": 13,
            "icon": "󰍳",
            "command": "prismlauncher",
            "class": "org.prismlauncher.PrismLauncher",
            "color": "#1abc9c",
        },
        "steam": {
            "enabled": True,
            "workspace": 14,
            "icon": "󰓓",
            "command": "steam",
            "class": "steam",
            "color": "#1e88e5",
        },
    },

    # Animation settings
    "animation_duration": 400,
    "animation_easing": "ease_out_cubic",  # See Animator.EASE_* constants
    "animation_fps": 60,
    "enable_animations": True,

    # Popup settings
    "popup_width": 400,
    "popup_margin_top": 8,
    "popup_margin_right": 20,
    "popup_slide_distance": 30,

    # Clock settings
    "clock_format": "%H:%M:%S",
    "clock_show_date": True,
    "clock_date_format": "%A, %B %d",
    "clock_update_interval": 1000,  # ms

    # Workspaces
    "workspaces_count": 5,  # Number of always-visible workspaces
    "workspaces_dynamic_max": 10,  # Max dynamic workspaces

    # Wallpaper settings
    "wallpapers_dir": "~/dotfiles/wallpapers",
    "matugen_scheme": "scheme-tonal-spot",

    # System metrics update intervals (ms)
    "metrics_cpu_interval": 2000,
    "metrics_memory_interval": 5000,
    "metrics_disk_interval": 30000,
    "metrics_network_interval": 1000,

    # Debounce settings
    "slider_debounce_ms": 50,

    # Appearance
    "font_family": "JetBrainsMono Nerd Font",
    "font_size": 13,
    "icon_size": 18,
    "border_radius": 12,
    "opacity": 0.85,
}


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from JSON file, merging with defaults.

    Args:
        config_path: Path to config file. Defaults to ~/.config/fabric/config.json

    Returns:
        Merged configuration dictionary
    """
    if config_path is None:
        config_path = os.path.expanduser("~/.config/fabric/config.json")

    # Start with defaults
    config = DEFAULTS.copy()

    # Deep copy nested dicts
    config["widgets_visible"] = DEFAULTS["widgets_visible"].copy()
    config["special_workspaces"] = {
        k: v.copy() for k, v in DEFAULTS["special_workspaces"].items()
    }

    # Load user config if exists
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                user_config = json.load(f)

            # Merge user config with defaults (user values override)
            for key, value in user_config.items():
                if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                    # Merge nested dicts
                    config[key].update(value)
                else:
                    config[key] = value

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config from {config_path}: {e}")

    return config


def save_config(config: Dict[str, Any], config_path: str = None) -> bool:
    """
    Save configuration to JSON file.

    Args:
        config: Configuration dictionary to save
        config_path: Path to config file

    Returns:
        True if saved successfully
    """
    if config_path is None:
        config_path = os.path.expanduser("~/.config/fabric/config.json")

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True

    except IOError as e:
        print(f"Error saving config: {e}")
        return False


class Config(Service):
    """
    Configuration service providing typed access to settings.
    Emits signals when configuration changes.
    """

    @Signal
    def changed(self, key: str) -> None:
        """Emitted when a configuration value changes"""
        pass

    @Signal
    def reloaded(self) -> None:
        """Emitted when configuration is reloaded from disk"""
        pass

    _instance = None

    @classmethod
    def get_instance(cls) -> "Config":
        """Get the singleton Config instance"""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    def __init__(self, config_path: str = None, **kwargs):
        super().__init__(**kwargs)
        self._config_path = config_path or os.path.expanduser("~/.config/fabric/config.json")
        self._config = load_config(self._config_path)

    def reload(self) -> None:
        """Reload configuration from disk"""
        self._config = load_config(self._config_path)
        self.emit("reloaded")

    def save(self) -> bool:
        """Save current configuration to disk"""
        return save_config(self._config, self._config_path)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """Set a configuration value"""
        self._config[key] = value
        self.emit("changed", key)
        if save:
            self.save()

    # Typed property accessors

    @Property(str, "readable", default_value="top")
    def bar_position(self) -> str:
        return self._config.get("bar_position", "top")

    @Property(int, "readable", default_value=4)
    def bar_margin(self) -> int:
        return self._config.get("bar_margin", 4)

    @Property(int, "readable", default_value=0)
    def bar_monitor(self) -> int:
        return self._config.get("bar_monitor", 0)

    @property
    def widgets_visible(self) -> Dict[str, bool]:
        return self._config.get("widgets_visible", DEFAULTS["widgets_visible"])

    @property
    def special_workspaces(self) -> Dict[str, Dict[str, Any]]:
        return self._config.get("special_workspaces", DEFAULTS["special_workspaces"])

    @Property(int, "readable", default_value=400)
    def animation_duration(self) -> int:
        return self._config.get("animation_duration", 400)

    @Property(str, "readable", default_value="ease_out_cubic")
    def animation_easing(self) -> str:
        return self._config.get("animation_easing", "ease_out_cubic")

    @Property(int, "readable", default_value=60)
    def animation_fps(self) -> int:
        return self._config.get("animation_fps", 60)

    @Property(bool, "readable", default_value=True)
    def enable_animations(self) -> bool:
        return self._config.get("enable_animations", True)

    @Property(int, "readable", default_value=400)
    def popup_width(self) -> int:
        return self._config.get("popup_width", 400)

    @Property(int, "readable", default_value=8)
    def popup_margin_top(self) -> int:
        return self._config.get("popup_margin_top", 8)

    @Property(int, "readable", default_value=20)
    def popup_margin_right(self) -> int:
        return self._config.get("popup_margin_right", 20)

    @Property(int, "readable", default_value=30)
    def popup_slide_distance(self) -> int:
        return self._config.get("popup_slide_distance", 30)

    @Property(str, "readable", default_value="%H:%M:%S")
    def clock_format(self) -> str:
        return self._config.get("clock_format", "%H:%M:%S")

    @Property(bool, "readable", default_value=True)
    def clock_show_date(self) -> bool:
        return self._config.get("clock_show_date", True)

    @Property(int, "readable", default_value=100)
    def clock_update_interval(self) -> int:
        return self._config.get("clock_update_interval", 1000)

    @Property(int, "readable", default_value=5)
    def workspaces_count(self) -> int:
        return self._config.get("workspaces_count", 5)

    @Property(int, "readable", default_value=10)
    def workspaces_dynamic_max(self) -> int:
        return self._config.get("workspaces_dynamic_max", 10)

    @Property(str, "readable", default_value="~/dotfiles/wallpapers")
    def wallpapers_dir(self) -> str:
        path = self._config.get("wallpapers_dir", "~/dotfiles/wallpapers")
        return os.path.expanduser(path)

    @Property(str, "readable", default_value="scheme-tonal-spot")
    def matugen_scheme(self) -> str:
        return self._config.get("matugen_scheme", "scheme-tonal-spot")

    @Property(int, "readable", default_value=50)
    def slider_debounce_ms(self) -> int:
        return self._config.get("slider_debounce_ms", 50)

    @Property(str, "readable", default_value="JetBrainsMono Nerd Font")
    def font_family(self) -> str:
        return self._config.get("font_family", "JetBrainsMono Nerd Font")

    @Property(int, "readable", default_value=13)
    def font_size(self) -> int:
        return self._config.get("font_size", 13)

    @Property(int, "readable", default_value=18)
    def icon_size(self) -> int:
        return self._config.get("icon_size", 18)

    @Property(int, "readable", default_value=12)
    def border_radius(self) -> int:
        return self._config.get("border_radius", 12)

    @Property(float, "readable", default_value=0.85)
    def opacity(self) -> float:
        return self._config.get("opacity", 0.85)

    def get_easing_curve(self) -> tuple:
        """Get the bezier curve for the configured easing"""
        from .animator import Animator

        easing_map = {
            "linear": Animator.EASE_LINEAR,
            "ease_in": Animator.EASE_IN,
            "ease_out": Animator.EASE_OUT,
            "ease_in_out": Animator.EASE_IN_OUT,
            "ease_out_cubic": Animator.EASE_OUT_CUBIC,
            "ease_out_back": Animator.EASE_OUT_BACK,
            "ease_out_expo": Animator.EASE_OUT_EXPO,
            "ease_in_out_cubic": Animator.EASE_IN_OUT_CUBIC,
        }

        easing_name = self.animation_easing.lower().replace("-", "_")
        return easing_map.get(easing_name, Animator.EASE_OUT_CUBIC)


# Global singleton accessor
config = None


def get_config() -> Config:
    """Get the global Config instance"""
    global config
    if config is None:
        config = Config.get_instance()
    return config
