#!/bin/bash
# Thin wrapper kept for muscle memory — the real logic (image vs video,
# matugen colors, backend swap) lives in ~/.config/matugen/set-wallpaper.sh
exec "$HOME/.config/matugen/set-wallpaper.sh" "$@"
