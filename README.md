# calibre-plugins

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/RobBrazier/calibre-plugins/build.yaml)
[![Codecov](https://img.shields.io/codecov/c/gh/RobBrazier/calibre-plugins)](https://app.codecov.io/gh/RobBrazier/calibre-plugins)
[![Codacy grade](https://img.shields.io/codacy/grade/11d6e5b88f054995b0321f5437042cf4)](https://app.codacy.com/gh/RobBrazier/calibre-plugins/dashboard)


## Current Plugins

- [Hardcover](./plugins/hardcover/)

## Local Setup

Local setup is automated via [mise-en-place](https://mise.jdx.dev/).
NOTE: You don't have to use this, just makes things more reproducible and
isolates your main calibre library from development

You can see all available scripts with `task list`

You can absolutely run without devenv or nix though - this just makes the
calibre environment portable and isolated from your main one

### Required tools:

#### Installed via Mise
1. [uv](https://docs.astral.sh/uv/)
2. [task](https://taskfile.dev/) (mentioned above)
3. [pre-commit](https://pre-commit.com/)
4. Python (uv can install this for you with `uv python install`)

#### Install externally
1. Calibre (you'll want to add the calibre library to your PYTHONPATH for
   a good IDE/editor experience)
