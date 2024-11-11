{ pkgs, lib, config, inputs, ... }:
{
  env.PYTHONPATH = "${config.devenv.dotfile}/profile/lib/calibre";
  env.CALIBRE_CONFIG_DIRECTORY = "${config.devenv.dotfile}/config/calibre";
  env.CALIBRE_TEMP_DIR = "${config.devenv.dotfile}/temp/calibre";
  env.CALIBRE_NO_DEFAULT_PROGRAMS = "1";
  env.CALIBRE_LIBRARY = "${config.devenv.dotfile}/state/calibre";
  env.UV_CACHE_DIR = "${config.devenv.dotfile}/cache/uv";

  # https://devenv.sh/packages/
  packages = [
    # Base packages
    pkgs.wget
    # Calibre
    pkgs.calibre
    # Utilities
    pkgs.go-task
    pkgs.toml-cli
    pkgs.jq
  ];

  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    package = pkgs.python39;
    uv.enable = true;
  };

  enterShell = ''
    uv venv --allow-existing
    source "${config.devenv.dotfile}/state/venv/bin/activate"
    task install
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  # enterTest = ''
  #   echo "Running tests"
  #   uv run pytest
  # '';

  # https://devenv.sh/pre-commit-hooks/
  pre-commit.hooks = {
    ruff.enable = true;
    ruff-format.enable = true;
    markdownlint.enable = true;
  };

  # See full reference at https://devenv.sh/reference/options/
}
