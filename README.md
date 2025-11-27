# calibre-plugins

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/RobBrazier/calibre-plugins/build.yaml)
[![Sonar Coverage](https://img.shields.io/sonar/coverage/RobBrazier_calibre-plugins?server=https%3A%2F%2Fsonarcloud.io)](https://sonarcloud.io/summary/new_code?id=RobBrazier_calibre-plugins)
[![Sonar Quality Gate](https://img.shields.io/sonar/quality_gate/RobBrazier_calibre-plugins?server=https%3A%2F%2Fsonarcloud.io)](https://sonarcloud.io/summary/new_code?id=RobBrazier_calibre-plugins)

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
2. [just](https://just.systems) - Task Runner
3. Python (uv can install this for you with `uv python install`)

#### Install externally

1. Calibre - to install/run the plugins - Calibre source is downloaded in
   `just .calibre/source` (called in `just install`)

### Running Tests Locally

Tests are run with unstubbed calibre libraries - most of the required config is
setup by `just setenv` (part of `just install`), however if you are running
tests outside of `just test`, one manual tweak is needed:

- Linux / Mac (maybe): you'll need to set `LD_LIBRARY_PATH` to the value of
  `CALIBRE_LIBRARY_PATH` environment variable (in .env file)
