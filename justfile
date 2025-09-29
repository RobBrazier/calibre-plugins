set dotenv-load := true

# list available tasks
list:
    @just --list

# Install dependencies and configure pre-commit hooks
install: && setenv
    uv sync --all-packages
    uv run lefthook install
    just .calibre/source

# Write to .env with your calibre configuration
setenv:
    -calibre-debug scripts/build_env.py

# Run unit tests
test *ARGS:
    LD_LIBRARY_PATH="$CALIBRE_LIBRARY_PATH" uv run pytest {{ARGS}}

# Run linters
lint:
    uv run ruff check --fix
    uv run pymarkdownlnt fix **/*.md

# Remove temporary files/directories
clean:
    -rm -rv dist
    find . -maxdepth 1 -name '.*cache' -type d -exec rm -rv "{}" \;
    find . -depth -name '*pycache*' -o -name '*.egg-info' -o -name 'build' -type d -exec rm -rv "{}" \;

# Build the specified plugin
build PLUGIN:
    bash scripts/bundle.sh {{PLUGIN}}

# Build all plugins
build-all:
    #!/usr/bin/env sh
    for name in $(ls plugins); do
        just build $name
    done

# Build and install a single plugin
install-plugin PLUGIN:
    just build {{PLUGIN}}
    find dist -name {{PLUGIN}}*.zip | xargs calibre-customize --add-plugin

# Build and install all plugins
install-plugins:
    #!/usr/bin/env sh
    for name in $(ls plugins); do
        just install-plugin $name
    done

run PLUGIN *ARGS:
    #!/usr/bin/env sh
    if [[ ! -f ".calibre/config/plugins/{{titlecase(PLUGIN)}}.zip" ]]; then
        just install-plugin {{PLUGIN}}
    fi
    just .calibre/run -r {{titlecase(PLUGIN)}} -- {{ARGS}}

calibre *ARGS:
    just .calibre/run -g {{ARGS}}

bump PLUGIN:
    bash scripts/bump.sh {{PLUGIN}}
