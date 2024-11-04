#!/usr/bin/env bash

set -euo pipefail

dist_base="$(pwd)/dist"
temp_base="$(pwd)/.build"

mkdir -p "$temp_base" "$dist_base"
rm -r "${temp_base:?}"/* "${dist_base:?}"/* || true

package_src() {
	path="$1"
	name="$(basename "$path")"

	temp="$temp_base/$name/"
	# Copy to build dir
	cp -r "$path/" "$temp"

	find "$temp" -name '__pycache__' -type d -print0 | xargs -0 rm -r

	requirements="$temp/requirements.txt"
	
	if [[ -f "$requirements" ]]; then
		# fix imports for dependencies
		# while read line; do
		# 	package="$(echo $line | cut -d '=' -f 1)"
		# 	find . -type f -name '*.py' | xargs sed -i "s/^import $package/from $name import $package/g"
		# 	find . -type f -name '*.py' | xargs sed -i "s/^from $package/from $name.$package/g"
		# done <$requirements
		pip install -r "$temp/requirements.txt" -t "$temp"
	fi

	if ! [ "$name" = "common" ]; then
		cd "$temp"
		# Create plugin txt file
		touch "plugin-import-name-$name.txt"

		# Replace imports
		cp -r "$temp_base/common" "$temp"
		find . -type f -name '*.py' -print0 | xargs -0 sed -i "s/from $name/from calibre_plugins.$name/g"
		find . -type f -name '*.py' -print0 | xargs -0 sed -i "s/from common/from calibre_plugins.$name.common/g"
	fi
}

#Package common
package_src "src/common"

# Package plugins
for plugin in src/*; do
	name="$(basename "$plugin")"
	if [ "$name" = "common" ]; then
		continue
	fi
	package_src "$plugin"
	cd "$temp_base/$name"

	zip -rq "$dist_base/$name.zip" . -x '*/__pycache__/*' '**/*.pyc'
done
