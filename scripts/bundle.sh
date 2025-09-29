#!/usr/bin/env bash

base_dir="$(pwd)"
dist_dir="$base_dir/dist"
plugins_dir="$base_dir/plugins"

plugin_name="$1"
package_name="${plugin_name/-/_}"
if [ -z "$plugin_name" ]; then
	echo "Usage: $0 <plugin>"
	exit 1
fi

plugin_dir="$plugins_dir/$plugin_name"
if [ ! -d "$plugin_dir" ]; then
	echo "Plugin directory $plugin_dir doesn't exist"
	exit 1
fi

if [ ! -d "$dist_dir" ]; then
	echo "Creating output directory $dist_dir"
	mkdir -p "$dist_dir"
fi

build_dir="$(mktemp -d)"
echo "Created build directory $build_dir"
trap "rm -r '$build_dir' || true" EXIT

# Get local dependencies (e.g. lib/*)
workspace_deps=($(uv export --package "$plugin_name" --no-header --no-annotate --format requirements.txt --no-emit-project --no-hashes | grep '-e ./' | cut -d ' ' -f 2))

# Install plugin dependencies to build dir
uv pip install "$plugin_dir" --target "$build_dir" --link-mode copy

# Install local dependencies
for dep in ${workspace_deps[@]}; do
	uv pip install "$dep" --target "$build_dir" --link-mode copy
done

# Move the plugin into root
mv "$build_dir/$package_name/"* "$build_dir"

version="$(grep -e '^Version:' "$build_dir/$package_name"*.dist-info/METADATA | cut -d ' ' -f 2)"

# Clean up unwanted files
find "$build_dir" -depth \( -name '*.dist-info' -o -name '.lock' -o -name '__pycache__' \) -exec rm -r "{}" \;
# Delete empty directories
find "$build_dir" -type d -empty -delete
touch "$build_dir/plugin-import-name-$package_name.txt"

find "$build_dir" -type f -name "$plugin_name-*.zip" -delete
out_zip="$dist_dir/$plugin_name-$version.zip"
(
	cd "$build_dir"
	zip -rq "$out_zip" .
)
echo "Bundled $plugin_name plugin to $out_zip"
