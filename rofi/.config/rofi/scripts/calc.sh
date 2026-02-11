#!/bin/bash
# Calculator using qalc, bc, or python3 as fallback

SCRIPTS_DIR="$HOME/.config/rofi/scripts"

# Check available calculator
if command -v qalc &> /dev/null; then
    CALC_CMD="qalc"
elif command -v bc &> /dev/null; then
    CALC_CMD="bc"
else
    CALC_CMD="python3"
fi

result=""
while true; do
    if [[ -n "$result" ]]; then
        prompt="= $result"
    else
        prompt="  Calc"
    fi

    input=$(rofi -dmenu -p "$prompt" \
        -theme-str 'listview { enabled: false; }')

    exit_code=$?

    # Left (exit 10) or Escape (exit 1) = go back to main menu
    [[ $exit_code -eq 10 || $exit_code -eq 1 ]] && exec "$SCRIPTS_DIR/main-menu.sh"

    [[ -z "$input" ]] && exit 0

    # Calculate result
    case "$CALC_CMD" in
        qalc)
            result=$(qalc -t "$input" 2>/dev/null)
            ;;
        bc)
            result=$(echo "$input" | bc -l 2>/dev/null)
            ;;
        python3)
            result=$(python3 -c "print($input)" 2>/dev/null)
            ;;
    esac
done
