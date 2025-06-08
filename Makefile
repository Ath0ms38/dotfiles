.PHONY: all install uninstall waybar hyprland swaync zsh starship kitty restart-waybar

all: install

install:
	@echo "Installing all dotfiles..."
	stow --target=$(HOME) --restow waybar
	stow --target=$(HOME) --restow hyprland
	stow --target=$(HOME) --restow swaync
	stow --target=$(HOME) --restow zsh
	stow --target=$(HOME) --restow starship
	stow --target=$(HOME) --restow kitty
	chmod +x ~/.config/waybar/scripts/*
	chmod +x ~/.config/fabric/*
	@echo "Dotfiles installed successfully!"

uninstall:
	@echo "Uninstalling dotfiles..."
	stow --target=$(HOME) --delete waybar
	stow --target=$(HOME) --delete hyprland
	stow --target=$(HOME) --delete swaync
	stow --target=$(HOME) --delete zsh
	stow --target=$(HOME) --delete starship
	stow --target=$(HOME) --delete kitty
	@echo "Dotfiles uninstalled successfully!"

waybar:
	stow --target=$(HOME) --restow waybar
	chmod +x ~/.config/waybar/scripts/*

hyprland:
	stow --target=$(HOME) --restow hyprland

swaync:
	stow --target=$(HOME) --restow swaync

zsh:
	stow --target=$(HOME) --restow zsh

starship:
	stow --target=$(HOME) --restow starship

kitty:
	stow --target=$(HOME) --restow kitty

restart-waybar:
	pkill waybar || true
	waybar &

help:
	@echo "Available targets:"
	@echo "  install     - Install all dotfiles"
	@echo "  uninstall   - Uninstall all dotfiles"
	@echo "  waybar      - Install only waybar config"
	@echo "  hyprland    - Install only hyprland config"
	@echo "  swaync      - Install only swaync config"
	@echo "  zsh         - Install only zsh config"
	@echo "  starship    - Install only starship config"
	@echo "  kitty       - Install only kitty config"
	@echo "  restart-waybar - Restart waybar"
