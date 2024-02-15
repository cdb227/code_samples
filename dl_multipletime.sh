#!/bin/bash

# Define variables
DATE='20240214' # date of fcast init.
TIME_RANGE=($(seq 0 6 48)) #validation times (from fcast init)

#TODO: pass LEVS and VARS as argument for flexibility

# Loop over the array of times
for TIME in "${TIME_RANGE[@]}"; do
    bash dl_singletime.sh "$TIME" "$DATE"
done