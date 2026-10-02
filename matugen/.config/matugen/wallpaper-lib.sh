#!/bin/bash
# Shared wallpaper helpers — sourced by set-wallpaper.sh, post-matugen.sh
# and restore-wallpaper.sh.
#
# Two backends:
#   images -> hyprpaper (static, cheap)
#   videos -> mpvpaper  (mpv rendered on the background layer)
#
# Matugen only reads images, and neither does hyprlock, so a video wallpaper
# is tracked as two paths: the "source" (what actually gets displayed) and
# the "still" (first frame, extracted with ffmpeg) used for colors, the lock
# screen background and thumbnails.

WALL_CACHE="$HOME/.cache/wallpaper"
WALL_FRAMES="$WALL_CACHE/frames"
WALL_STATE="$WALL_CACHE/state"

WALL_VIDEO_EXTS="mp4 mkv webm mov avi m4v"
WALL_IMAGE_EXTS="png jpg jpeg bmp gif webp"

# panscan=1.0 mimics hyprpaper's `fit_mode = cover`.
WALL_MPV_OPTS="no-audio loop-file=inf hwdec=auto panscan=1.0"

wall_is_video() {
    local ext="${1##*.}"
    [[ " $WALL_VIDEO_EXTS " == *" ${ext,,} "* ]]
}

wall_is_wallpaper() {
    local ext="${1##*.}"
    ext="${ext,,}"
    [[ " $WALL_VIDEO_EXTS $WALL_IMAGE_EXTS " == *" $ext "* ]]
}

# wall_still <path> — echo an image representing <path>: the file itself for
# images, a cached first frame for videos. Non-zero if extraction failed.
wall_still() {
    local src="$1"
    wall_is_video "$src" || { printf '%s\n' "$src"; return 0; }

    mkdir -p "$WALL_FRAMES"
    local key frame
    key="$(printf '%s' "$src" | md5sum | cut -d' ' -f1)"
    frame="$WALL_FRAMES/$key.png"

    if [ ! -s "$frame" ] || [ "$src" -nt "$frame" ]; then
        # Seek 1s in first — plenty of videos open on a black frame, which
        # would give matugen a monochrome palette.
        ffmpeg -y -loglevel error -ss 1 -i "$src" -frames:v 1 "$frame" 2>/dev/null
        [ -s "$frame" ] ||
            ffmpeg -y -loglevel error -i "$src" -frames:v 1 "$frame" 2>/dev/null
    fi

    [ -s "$frame" ] || return 1
    printf '%s\n' "$frame"
}

# wall_state <source|still|kind> — read one field of the saved state.
wall_state() {
    [ -f "$WALL_STATE" ] || return 1
    local line
    line="$(grep -m1 "^$1=" "$WALL_STATE")" || return 1
    printf '%s\n' "${line#*=}"
}

# wall_state_write <source> <still> — record the intended wallpaper. Called
# before matugen runs so its post_hook knows what it is really applying.
wall_state_write() {
    mkdir -p "$WALL_CACHE"
    {
        printf 'source=%s\n' "$1"
        printf 'still=%s\n' "$2"
        printf 'kind=%s\n' "$(wall_is_video "$1" && echo video || echo image)"
    } > "$WALL_STATE"
}

wall_write_hyprpaper_conf() {
    cat > "$HOME/.config/hypr/hyprpaper.conf" << EOF
# Wallpaper for all monitors (set by matugen)
wallpaper {
    monitor =
    path = $1
    fit_mode = cover
}

# Misc options
ipc = true
splash = false
splash_offset = 20
splash_opacity = 0.8
EOF
}

# wall_apply <source> <still> — swap to the right backend and display it.
wall_apply() {
    local src="$1" still="$2"

    if wall_is_video "$src"; then
        pkill -x hyprpaper 2>/dev/null
        pkill -x mpvpaper 2>/dev/null
        sleep 0.2
        # -p pauses decoding under a fullscreen window (saves battery)
        setsid mpvpaper -p -o "$WALL_MPV_OPTS" '*' "$src" >/dev/null 2>&1 &
    else
        pkill -x mpvpaper 2>/dev/null
        wall_write_hyprpaper_conf "$src"
        pkill -x hyprpaper 2>/dev/null
        sleep 0.2
        setsid hyprpaper >/dev/null 2>&1 &
    fi

    # Consumers that always want a picture, never a video
    printf '%s' "$still" > "$HOME/.cache/current_wallpaper"
    ln -sfn "$src" "$HOME/.current.wall"

    wall_state_write "$src" "$still"
}
