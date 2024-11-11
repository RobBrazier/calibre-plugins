#!/usr/bin/env bash
directory="$1"

config_file="$1/pyproject.toml"
dependencies=($(toml get "$config_file" "project.dependencies" | jq -r '.[]'))
for dep in "${dependencies[@]}"; do
	info="$(uv pip show "$dep" 2>&1)"
	echo "$info"
	location="$(echo "$info" | grep Location | awk -F':' '{ print $2 }' | xargs echo)/${dep}"
	if echo "$info" | grep -cq "Editable"; then
		local=1
		location="$(echo "$info"|  grep -i 'editable project location' | awk -F':' '{ print $2 }' | xargs echo)"
	fi
	echo "$location"
done
