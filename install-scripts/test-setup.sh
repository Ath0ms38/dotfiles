#!/usr/bin/env bash
set -euo pipefail

# Check for AGS binary
if ! command -v ags &> /dev/null; then
  echo "Error: AGS is not installed or not in PATH."
  exit 1
fi

# Check for Astal libraries (libgtk-4, libadwaita-1)
for lib in libgtk-4.so libadwaita-1.so; do
  if ! ldconfig -p | grep -q "$lib"; then
    echo "Error: $lib not found. Please install the required library."
    exit 1
  fi
done

# Check AGS config presence
if [ ! -f "$HOME/.config/ags/app.ts" ]; then
  echo "Error: AGS config (app.ts) not found in ~/.config/ags."
  exit 1
fi

# Check TypeScript types
pushd ags/.config/ags > /dev/null
if ! npx tsc --noEmit; then
  echo "Error: TypeScript type check failed in AGS config."
  popd > /dev/null
  exit 1
fi
popd > /dev/null

# Start AGS in test mode
echo "Starting AGS in test mode..."
ags --config "$HOME/.config/ags/app.ts" --test &

sleep 2

# Check waybar integration
if pgrep -x "waybar" > /dev/null; then
  echo "Waybar is running. Checking AGS integration..."
  # Example check: look for AGS IPC socket or integration file
  if [ ! -S "/tmp/ags-ipc.sock" ]; then
    echo "Warning: AGS IPC socket not found. Integration may not be active."
  else
    echo "AGS IPC socket found. Integration looks good."
  fi
else
  echo "Waybar is not running. Skipping integration check."
fi

echo "Test setup complete."