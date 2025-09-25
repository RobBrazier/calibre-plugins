# calibre-plugins

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/RobBrazier/calibre-plugins/build.yaml)
[![Codecov](https://img.shields.io/codecov/c/gh/RobBrazier/calibre-plugins)](https://app.codecov.io/gh/RobBrazier/calibre-plugins)
[![Codacy grade](https://img.shields.io/codacy/grade/11d6e5b88f054995b0321f5437042cf4)](https://app.codacy.com/gh/RobBrazier/calibre-plugins/dashboard)

## Current Plugins

- [Hardcover](./plugins/hardcover/): Metadata Plugin for Hardcover.app
- [Manga Chapter Extractor](./plugins/manga-chapters/) Editor Plugin for
extracting Manga chapters from the Contents page

## Local Setup

Local setup is automated via [mise-en-place](https://mise.jdx.dev/).
NOTE: You don't have to use this, just makes things more reproducible and
isolates your main calibre library from development

You can see all available scripts with `task list`

### Required tools

#### Installed via Mise

1. [uv](https://docs.astral.sh/uv/) - Python Package Manager
2. [task](https://taskfile.dev/) - Task Runner
3. Python (uv can install this for you with `uv python install`)

#### Install externally

1. Calibre - to install/run the plugins - Calibre source is downloaded in
   `task calibre:source` (called in `task install`)

### Running Tests Locally

Tests are run with unstubbed calibre libraries - most of the required config is
setup by `task setenv` (part of `task install`), however if you are running
tests outside of `task test`, one manual tweak is needed:

- Linux / Mac (maybe): you'll need to set `LD_LIBRARY_PATH` to the value of
  `CALIBRE_LIBRARY_PATH` environment variable (in .env file)
