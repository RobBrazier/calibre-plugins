# calibre-plugins

## Current Plugins

- [Hardcover](./plugins/hardcover/)

## Local Setup

Local setup is automated via [devenv.sh](https://devenv.sh) and [Nix](https://nixos.org)

[`task`](https://taskfile.dev) is pre-installed in the environment and used for
task running

You can see all available scripts with `task list`

You can absolutely run without devenv or nix though - this just makes the
calibre environment portable and isolated from your main one

Tools required:

1. [uv](https://docs.astral.sh/uv/)
2. task (mentioned above)
3. Python (uv can install this for you with `uv python install`)
4. Calibre (you'll want to add the calibre library to your PYTHONPATH for
   a good IDE/editor experience)
