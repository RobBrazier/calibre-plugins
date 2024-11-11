# calibre-plugins

## Local Setup

Environment setup is fully done via [devenv.sh](https://devenv.sh) and [Nix](https://nixos.org)

## Development Scripts

### install

Install all dependenices

```bash
task install
```

### calibre:setup

Downloads free books from the gutenberg project and sets up calibre within the
nix environment

```bash
task calibre:setup
```

### calibre:run

Launches calibre in debug mode - exactly the same as `calibre-debug -g`, just a
utility method

```bash
task calibre:run
```

### package:plugin

Packages the plugin including dependencies as a zip file

```bash
task package:PLUGIN
# e.g. task package:hardcover
```

### install:plugin

Installs the plugin zip to calibre

```bash
task install:PLUGIN
# e.g. task install:hardcover
```

### run:plugin

Packages and installs the hardcover plugin, then launching the plugin in
calibre cli mode

```bash
task run:PLUGIN -- t:BOOK_TITLE a:BOOK_AUTHORS i:BOOK_IDENTIFIERS
# e.g. task run:hardcover -- t:BOOK_TITLE a:BOOK_AUTHORS i:BOOK_IDENTIFIERS
```
