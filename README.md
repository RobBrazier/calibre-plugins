# calibre-plugins

## Development Scripts

### setup-calibre

Downloads free books from the gutenberg project and sets up calibre within the
nix environment

```bash
setup-calibre
```

### package

Packages the plugin including dependencies as a zip file

```bash
package PLUGIN_NAME
# e.g. package hardcover
```

### install-plugin

Installs the plugin zip to calibre

```bash
install-plugin PLUGIN_NAME
# e.g. install-plugin hardcover
```

## run-hardcover

Packages and installs the hardcover plugin, then launching the plugin in
calibre cli mode

```bash
run-hardcover t:BOOK_TITLE a:BOOK_AUTHORS i:BOOK_IDENTIFIERS
```
