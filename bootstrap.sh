#!/bin/bash
# Bootstrap script — sets up the full desktop environment from this repo
# on a fresh Arch install. Safe to re-run (idempotent where possible).
#
# Usage:  ./bootstrap.sh
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/dotfiles-backup-$(date +%Y%m%d-%H%M%S)"

# Stow packages to link into $HOME (ags is legacy — fabric replaced it)
STOW_PACKAGES=(fabric fastfetch hyprland kitty matugen rofi starship swaync zsh)

PACMAN_PACKAGES=(
    # Hyprland ecosystem
    hyprland hyprpaper hypridle hyprlock hyprsunset xdg-desktop-portal-hyprland
    # Terminal, shell, prompt
    kitty zsh starship
    # CLI tools used by .zshrc and scripts
    eza bat ripgrep fd fzf jq stow git fastfetch
    # Python toolchain (fabric bar runs in a uv-managed venv)
    uv python gobject-introspection cairo pkgconf base-devel
    # Desktop services
    swaync rofi cliphist wl-clipboard brightnessctl playerctl
    pipewire wireplumber networkmanager
    # Screenshots
    hyprshot grim slurp
    # Apps
    nautilus firefox
    # Login screen (SDDM + theme runtime deps for QML/video backgrounds)
    sddm qt6-multimedia qt6-svg qt6-virtualkeyboard qt6ct
    # Look & feel
    adw-gtk-theme ttf-jetbrains-mono-nerd noto-fonts
)

AUR_PACKAGES=(
    matugen-git      # wallpaper -> color scheme generator
    kando-bin        # radial menu (ctrl+space)
    hyprshot-gui-git # screenshot GUI (super+shift+s)
)

msg() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------- packages
msg "Installing official packages"
sudo pacman -S --needed --noconfirm "${PACMAN_PACKAGES[@]}"

if ! command -v yay >/dev/null; then
    msg "Installing yay (AUR helper)"
    tmp="$(mktemp -d)"
    git clone https://aur.archlinux.org/yay-bin.git "$tmp/yay-bin"
    (cd "$tmp/yay-bin" && makepkg -si --noconfirm)
    rm -rf "$tmp"
fi

msg "Installing AUR packages"
yay -S --needed --noconfirm "${AUR_PACKAGES[@]}"

# ---------------------------------------------------------------- zsh / oh-my-zsh
msg "Setting up oh-my-zsh + plugins"
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git "$HOME/.oh-my-zsh"
fi
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
[ -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ] ||
    git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
[ -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ] ||
    git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"

if [ "$(basename "$SHELL")" != "zsh" ]; then
    msg "Changing default shell to zsh"
    chsh -s "$(command -v zsh)"
fi

# ---------------------------------------------------------------- stow
msg "Linking dotfiles with stow"
# Move real files/dirs out of the way so stow can link (symlinks are left alone)
backup_if_real() {
    local target="$1"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        mkdir -p "$BACKUP_DIR"
        echo "  backing up $target -> $BACKUP_DIR/"
        mv "$target" "$BACKUP_DIR/"
    fi
}
backup_if_real "$HOME/.zshrc"
backup_if_real "$HOME/.config/starship.toml"
for dir in fabric fastfetch hypr kitty matugen rofi swaync; do
    backup_if_real "$HOME/.config/$dir"
done

mkdir -p "$HOME/.config"
(cd "$DOTFILES" && stow --restow "${STOW_PACKAGES[@]}")

# ---------------------------------------------------------------- fabric bar
msg "Setting up fabric bar Python environment (uv)"
uv sync --project "$DOTFILES/fabric/.config/fabric"

# ---------------------------------------------------------------- login screen
msg "Installing SDDM theme + config"
"$DOTFILES/sddm/install.sh"
sudo tee /etc/sddm.conf >/dev/null <<'EOF'
[Theme]
Current=cozy-anime-room
EOF

msg "Enabling system services"
sudo systemctl enable sddm.service
sudo systemctl enable NetworkManager.service

# ---------------------------------------------------------------- done
msg "Done!"
echo "Notes:"
echo "  - Log out / reboot to start Hyprland from SDDM."
echo "  - Wallpapers live in $DOTFILES/wallpapers; set one via the fabric"
echo "    wallpaper picker (or matugen image <path>) to generate the color theme."
[ -d "$BACKUP_DIR" ] && echo "  - Pre-existing configs were backed up to $BACKUP_DIR"
