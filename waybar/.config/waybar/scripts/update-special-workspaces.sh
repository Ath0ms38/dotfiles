#!/bin/bash

# Simple script to update special workspace buttons in waybar
# Called by Hyprland on workspace changes

# Send signals to waybar to update special workspace modules
pkill -RTMIN+8 waybar   # Discord
pkill -RTMIN+9 waybar   # VSCode  
pkill -RTMIN+10 waybar  # Minecraft
