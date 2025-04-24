#!/usr/bin/env bash

tag="$1"
name="${tag%-*}"
version="${tag##*-}"

file="RELEASE_NOTES.md"

git cliff --config cliff.toml \
	--current --include-path "plugins/$name/**/*"  \
	--tag-pattern "$name-*" --tag "$tag" --output "$file"

contents="$(cat $file)"
rm "$file"
echo -e "Release Notes for $tag:\n$contents"

if [[ "$version" == *"pre"* ]]; then
	opts="--prerelease"
else
	opts="--latest"
fi

gh release create "$tag" $opts -n "$contents" -t "$tag" **/"$tag"*.zip
