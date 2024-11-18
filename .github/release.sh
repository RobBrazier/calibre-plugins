#!/usr/bin/env bash
TAG_REF="$1"
SOURCE_TAG="${TAG_REF#refs/tags/}"
PLUGIN_NAME="$(echo "$SOURCE_TAG" | awk -F'-' '{ print $1 }')"
PREVIOUS_TAG="$(git tag -n --sort=-version:refname "$PLUGIN_NAME-*" | grep -v "$SOURCE_TAG" | head -n 1 | awk '{ print $1 }')"
echo $PREVIOUS_TAG
VERSION="$(echo "$SOURCE_TAG" | awk -F'-' '{ print $2 }')"

echo "Creating release for $PLUGIN_NAME v$VERSION"

gh release create -d "$SOURCE_TAG" -t "$PLUGIN_NAME v$VERSION" --generate-notes --notes-start-tag "$PREVIOUS_TAG" "./$SOURCE_TAG"*.zip
