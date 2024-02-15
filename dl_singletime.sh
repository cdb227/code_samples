#!/bin/bash

# Define time parameter based on parameter passed when script called
TIME="$1"
DATE="$2"

# Define variables
ROOT_URL="https://data.ecmwf.int/forecasts/${DATE}/00z/0p4-beta/enfo/"

LEVS=("800" "1000")
VARS=("t" "u" "v")

echo "Running for TIME=${TIME}h"

# Download the index file
curl "${ROOT_URL}${DATE}000000-${TIME}h-enfo-ef.index" --output ${DATE}000000-${TIME}h-enfo-ef.index
INDEX_FILE="${DATE}000000-${TIME}h-enfo-ef.index"


# Construct the grep command with the pattern
VARpattern=$(printf "\"%s\"" "${VARS[0]}"; printf "|\"%s\"" "${VARS[@]:1}")
LEVpattern=$(printf "\"%s\"" "${LEVS[0]}"; printf "|\"%s\"" "${LEVS[@]:1}")

#echo $VARpattern

entries=$(grep -E "\"param\": ($VARpattern)" "$INDEX_FILE" | grep -E "\"levelist\": ($LEVpattern)")

# Initialize the variable to store the range strings
range_strings=""

# Iterate over each line of the grep result
while IFS= read -r entry; do
    # \s*: Matches zero or more whitespace characters (spaces, tabs, etc.).
    # \K: Resets the match so that only the part after \K is included in the output.
    # \d+: Matches one or more digits (0-9).
    _OFFSET=$(grep -oP '"_offset":\s*\K\d+' <<< "$entry")
    _LENGTH=$(grep -oP '"_length":\s*\K\d+' <<< "$entry")

    # Calculate start_bytes and end_bytes
    start_bytes=$_OFFSET
    end_bytes=$(( _OFFSET + _LENGTH - 1 ))

    # Append the range string to the variable
    if [ -z "$range_strings" ]; then
        # If range_strings is empty, set it to the first ranges
        range_strings="Range: bytes=${start_bytes}-${end_bytes}"
    else
        # If range_strings already has values, append the new range with a comma
        range_strings="${range_strings}, ${start_bytes}-${end_bytes}"
    fi
done <<< "$entries"

# Download the data files using the generated range strings
curl ${ROOT_URL}${DATE}000000-${TIME}h-enfo-ef.grib2 -H "$range_strings" --output ${DATE}-${TIME}h-ecmwf-ens.grib2
