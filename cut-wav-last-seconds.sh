#!/bin/bash

# Usage: ./trim_end_sox.sh input.wav [seconds_to_trim]
# Example: ./trim_end_sox.sh my_audio.wav 2

# --- Validate input arguments ---
if [ -z "$1" ]; then
    echo "Usage: $0 input.wav [seconds_to_trim]"
    exit 1
fi

INPUT="$1"
TRIM=${2:-1}  # Default is 1 second if not specified
OUTPUT="${INPUT%.wav}_trimmed.wav"

# --- Check required tools ---
for cmd in sox soxi; do
    if ! command -v $cmd >/dev/null 2>&1; then
        echo "Error: '$cmd' is not installed."
        exit 1
    fi
done

# --- Get duration of input file in seconds ---
DURATION=$(soxi -D "$INPUT")

if (( $(echo "$DURATION <= $TRIM" | bc -l) )); then
    echo "❌ The file is too short to trim $TRIM seconds (duration: $DURATION s)."
    exit 1
fi

# --- Calculate new duration and trim with sox ---
END=$(echo "$DURATION - $TRIM" | bc -l)
echo "✂️ Trimming the last $TRIM seconds from '$INPUT'..."
sox "$INPUT" "$OUTPUT" trim 0 =$END

echo "✅ Trimmed file saved as '$OUTPUT'"

