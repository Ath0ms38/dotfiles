#!/bin/bash
# Animated ASCII cat with fastfetch

# ASCII cat frames
FRAMES=(
'   \    /\
    )  ( '"'"')
   (  /  )
    \(__)|'

'   \    /\
    )  ( '"'"')
   (  /  )
   (__)/|'

'   \    /\
    )  ( '"'"')
   (  /  )
    |(__)'

'   \    /\
    )  ( '"'"')
   (  /  )
   |/(__)'
)

# Get fastfetch output (no logo)
FF_OUTPUT=$(fastfetch --logo none --pipe 2>/dev/null)

# Count lines
FF_LINES=$(echo "$FF_OUTPUT" | wc -l)
CAT_LINES=4

# Padding to center cat vertically relative to fastfetch output
PAD_TOP=$(( (FF_LINES - CAT_LINES) / 2 ))
[ $PAD_TOP -lt 0 ] && PAD_TOP=0

# Function to display a frame
display_frame() {
    local frame="$1"

    # Clear screen and hide cursor
    printf '\033[H\033[?25l'

    # Print top padding
    for ((i=0; i<PAD_TOP; i++)); do
        echo ""
    done

    # Combine cat and fastfetch line by line
    local cat_lines=()
    while IFS= read -r line; do
        cat_lines+=("$line")
    done <<< "$frame"

    local ff_lines=()
    while IFS= read -r line; do
        ff_lines+=("$line")
    done <<< "$FF_OUTPUT"

    local max_lines=${#ff_lines[@]}
    [ ${#cat_lines[@]} -gt $max_lines ] && max_lines=${#cat_lines[@]}

    for ((i=0; i<max_lines; i++)); do
        local cat_line=""
        local ff_line=""

        # Get cat line (with vertical offset)
        local cat_idx=$((i - PAD_TOP))
        if [ $cat_idx -ge 0 ] && [ $cat_idx -lt ${#cat_lines[@]} ]; then
            cat_line="${cat_lines[$cat_idx]}"
        fi

        # Get fastfetch line
        if [ $i -lt ${#ff_lines[@]} ]; then
            ff_line="${ff_lines[$i]}"
        fi

        # Print combined (cat is ~15 chars wide, add padding)
        printf "  %-18s %s\n" "$cat_line" "$ff_line"
    done
}

# Cleanup on exit
cleanup() {
    printf '\033[?25h'  # Show cursor
    exit 0
}
trap cleanup EXIT INT TERM

# Animation loop - run for ~3 seconds then stop
DURATION=3
FRAME_DELAY=0.2
END_TIME=$(($(date +%s) + DURATION))

while [ $(date +%s) -lt $END_TIME ]; do
    for frame in "${FRAMES[@]}"; do
        display_frame "$frame"
        sleep $FRAME_DELAY
        [ $(date +%s) -ge $END_TIME ] && break
    done
done

# Final static display
display_frame "${FRAMES[0]}"
printf '\033[?25h'  # Show cursor
echo ""
