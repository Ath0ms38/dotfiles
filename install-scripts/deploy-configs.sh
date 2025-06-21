#!/usr/bin/env bash
set -euo pipefail

# Backup existing configs
backup_dir="$HOME/.config-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir"
echo "Backing up existing configs to $backup_dir"
for dir in ags hyprland kitty starship swaync waybar zsh; do
  if [ -d "$HOME/.config/$dir" ]; then
    mv "$HOME/.config/$dir" "$backup_dir/" || true
  fi
done

# Deploy configs using stow
echo "Deploying configs with stow"
for dir in ags hyprland kitty starship swaync waybar zsh; do
  stow -t "$HOME/.config" "$dir"
done

# Install AGS dependencies
if [ -d "ags/.config/ags" ]; then
  echo "Installing AGS npm dependencies"
  pushd ags/.config/ags > /dev/null
  npm install
  npx tsc --noEmit
  popd > /dev/null
fi

# Update AGS TypeScript types
if [ -f "ags/.config/ags/package.json" ]; then
  echo "Updating AGS TypeScript types"
  pushd ags/.config/ags > /dev/null
  npm run types || true
  popd > /dev/null
fi

# Update Makefile timestamp
touch Makefile

echo "Deployment complete."