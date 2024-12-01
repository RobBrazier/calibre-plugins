#!/bin/bash

set -ue  # Exit on any error

# Function to show usage
usage() {
    echo "Usage: $0 <plugin-name>"
    echo "Example: $0 my-plugin"
    exit 1
}

# Check if yq is available
if ! command -v yq &> /dev/null; then
    echo "Error: yq is required but not installed"
    exit 1
fi

# Check if a plugin name was provided
if [ "$#" -ne 1 ]; then
    usage
fi

PLUGIN_NAME="$1"
PLUGIN_PACKAGE="${PLUGIN_NAME/-/_}"
PLUGIN_DIR="$(pwd)/plugins/$PLUGIN_NAME"

# Check if plugin directory exists
if [ ! -d "$PLUGIN_DIR" ]; then
    echo "Error: Plugin directory $PLUGIN_DIR does not exist"
    exit 1
fi

# Check if pyproject.toml exists
if [ ! -f "$PLUGIN_DIR/pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in $PLUGIN_DIR"
    exit 1
fi

# Get name and version from pyproject.toml
NAME="$(yq -r '.project.name' "$PLUGIN_DIR/pyproject.toml")"
VERSION="$(grep -F "__version__ = " "$PLUGIN_DIR/src/$PLUGIN_PACKAGE/_version.py" | cut -d'"' -f2)"

# Create dist directory if it doesn't exist
mkdir -p dist
find dist -name "$PLUGIN_NAME*.zip" -delete

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Create target directory
TARGET_DIR="$TEMP_DIR/$NAME"
mkdir -p "$TARGET_DIR"

# Install dependencies
if ! uv --directory "$PLUGIN_DIR" pip install . --target "$TARGET_DIR" --link-mode copy; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Move plugin source into root and clean up src
mv "$TARGET_DIR/$PLUGIN_PACKAGE/"* "$TARGET_DIR"
rm -r "$TARGET_DIR/$PLUGIN_PACKAGE"

# Clean extra files
rm -r "$TARGET_DIR"/*-info "$TARGET_DIR/.lock"

# Copy local dependencies
find "$TARGET_DIR" -name '_*.pth' -type f -print0 | 
    while IFS= read -r -d '' name; do 
        loc="$(cat $name | tr -d '[:space:]')"
        cp -r "$loc/"* "$TARGET_DIR"
        rm "$name"
    done

# Clean pycache
find "$TARGET_DIR" -name '__pycache__' -o -name '*.*-info' -type d | xargs -r rm -r

# Create plugin-import-name-$NAME.txt
touch "$TARGET_DIR/plugin-import-name-$PLUGIN_PACKAGE.txt"

# Create zip file from temp directory to dist
DIST_OUTPUT="$(pwd)/dist/$NAME-$VERSION.zip"
if [ -f "$DIST_OUTPUT" ]; then
    rm "$DIST_OUTPUT"
fi
cd "$TARGET_DIR" && zip -r "$DIST_OUTPUT" .

echo "Successfully created bundle at: $DIST_OUTPUT"
