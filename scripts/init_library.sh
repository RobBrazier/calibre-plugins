#!/usr/bin/env bash

books=(
	"https://www.gutenberg.org/ebooks/1513.epub.noimages" # Romeo and Juliet
)

for book in "${books[@]}"; do
	wget -P "$CALIBRE_TEMP_DIR" --no-clobber --content-disposition "$book"
done

for book in "$CALIBRE_TEMP_DIR"/*.epub; do
	calibredb add --with-library "$CALIBRE_LIBRARY" "$book"
	rm "$book"
done
