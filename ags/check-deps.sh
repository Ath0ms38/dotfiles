#!/usr/bin/env bash

# AGS v2 Complete Fix Guide - Step 1: Dependency Check Script

set -e

CORE_PKGS=(
  "gjs"
  "gtk3"
  "gtk-layer-shell"
  "libadwaita"
  "libappindicator-gtk3"
  "webkit2gtk"
  "gobject-introspection"
  "cairo"
  "pango"
  "gdk-pixbuf2"
  "json-glib"
  "libnotify"
  "glib2"
  "glibc"
)

AUR_PKGS=(
  "gtk4"
  "libadwaita"
  "libpanel"
)

GI_TYPELIBS=(
  "Gtk-3.0"
  "Gtk-4.0"
  "Adw-1"
  "GdkPixbuf-2.0"
  "WebKit2-4.0"
  "Notify-0.7"
  "AppIndicator3-0.1"
)

missing_core=()
for pkg in "${CORE_PKGS[@]}"; do
  if ! pacman -Q "$pkg" &>/dev/null; then
    missing_core+=("$pkg")
  fi
done

missing_aur=()
for pkg in "${AUR_PKGS[@]}"; do
  if ! pacman -Q "$pkg" &>/dev/null; then
    missing_aur+=("$pkg")
  fi
done

if [ ${#missing_core[@]} -ne 0 ]; then
  echo "Installing missing core packages: ${missing_core[*]}"
  sudo pacman -S --needed "${missing_core[@]}"
fi

if [ ${#missing_aur[@]} -ne 0 ]; then
  echo "Installing missing AUR packages: ${missing_aur[*]}"
  if command -v yay &>/dev/null; then
    yay -S --needed "${missing_aur[@]}"
  elif command -v paru &>/dev/null; then
    paru -S --needed "${missing_aur[@]}"
  else
    echo "No AUR helper found (yay or paru). Please install missing AUR packages manually: ${missing_aur[*]}"
    exit 1
  fi
fi

echo "Checking for required GObject Introspection Typelibs..."
missing_typelibs=()
for typelib in "${GI_TYPELIBS[@]}"; do
  if ! g-ir-inspect-1.0 "$typelib" &>/dev/null; then
    missing_typelibs+=("$typelib")
  fi
done

if [ ${#missing_typelibs[@]} -ne 0 ]; then
  echo "Missing GObject Typelibs: ${missing_typelibs[*]}"
  echo "Please ensure all required packages are installed."
  exit 1
fi

echo "All dependencies are satisfied."