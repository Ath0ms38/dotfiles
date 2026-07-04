#!/bin/bash
# Install SDDM theme by symlinking to system directory
# Requires sudo privileges

DOTFILES_THEME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/usr/share/sddm/themes/cozy-anime-room"
SYSTEM_THEME="/usr/share/sddm/themes/cozy-anime-room"

echo "Installing SDDM theme..."

# Remove existing theme (backup if it's not a symlink)
if [ -e "$SYSTEM_THEME" ] && [ ! -L "$SYSTEM_THEME" ]; then
    echo "Backing up existing theme to ${SYSTEM_THEME}.bak"
    sudo mv "$SYSTEM_THEME" "${SYSTEM_THEME}.bak"
elif [ -L "$SYSTEM_THEME" ]; then
    echo "Removing existing symlink..."
    sudo rm "$SYSTEM_THEME"
fi

# Create symlink
echo "Creating symlink: $SYSTEM_THEME -> $DOTFILES_THEME"
sudo ln -s "$DOTFILES_THEME" "$SYSTEM_THEME"

echo "Done! SDDM theme installed."
