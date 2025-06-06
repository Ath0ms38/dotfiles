#!/bin/bash

# Simple periodic monitor for special workspace changes
# This checks every few seconds but only when on special workspaces

# Function to update waybar buttons
update_buttons() {
    pkill -RTMIN+8 waybar   # Discord
    pkill -RTMIN+9 waybar   # VSCode  
    pkill -RTMIN+10 waybar  # Minecraft
}

# Function to check if we're on a special workspace
is_on_special_workspace() {
    local current_ws
    current_ws=$(hyprctl activeworkspace -j | jq -r '.id')
    [[ "$current_ws" == "11" || "$current_ws" == "12" || "$current_ws" == "13" ]]
}

# Store previous state
declare -A prev_state

# Function to get current app states including current workspace
get_app_states() {
    local discord_running vscode_running minecraft_running current_ws
    
    current_ws=$(hyprctl activeworkspace -j | jq -r '.id')
    discord_running=$(hyprctl clients -j | jq -r '.[] | select(.class=="discord") | .workspace.id' 2>/dev/null | head -1)
    vscode_running=$(hyprctl clients -j | jq -r '.[] | select(.class=="Code") | .workspace.id' 2>/dev/null | head -1)
    minecraft_running=$(hyprctl clients -j | jq -r '.[] | select(.class=="org.polymc.PolyMC") | .workspace.id' 2>/dev/null | head -1)
    
    echo "ws:${current_ws} discord:${discord_running:-0} vscode:${vscode_running:-0} minecraft:${minecraft_running:-0}"
}

echo "Starting special workspace monitor..."

# Initialize previous state
prev_state_str=$(get_app_states)

while true; do
    # More frequent polling for better responsiveness
    sleep 0.5
    
    # Get current state
    current_state_str=$(get_app_states)
    
    # Check if state changed
    if [[ "$current_state_str" != "$prev_state_str" ]]; then
        echo "State changed: $prev_state_str -> $current_state_str"
        update_buttons
        prev_state_str="$current_state_str"
    fi
done
