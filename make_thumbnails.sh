#!/bin/bash

mkdir -p tn
mkdir -p tn/images

# Loop through all matching files
for file in data/images/*.{jpg,jpeg,png}; do
    # Skip if glob doesn't match anything
    [ -e "$file" ] || continue

    # Extract just the filename (e.g., image.jpg)
    filename=$(basename "$file")

    # Create the thumbnail
    magick "$file" -thumbnail 300 "tn/images/$filename"
done

# Special case resize
mkdir -p tn/images
magick images/portrait_circle.png -resize 5000x5000 "tn/images/portrait_circle.jpg"
