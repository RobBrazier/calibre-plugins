{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  env = {
    PYTHONPATH = "${config.devenv.dotfile}/profile/lib/calibre";
    CALIBRE_CONFIG_DIRECTORY = "${config.devenv.dotfile}/config/calibre";
    CALIBRE_TEMP_DIR = "${config.devenv.dotfile}/temp/calibre";
    CALIBRE_NO_DEFAULT_PROGRAMS = "1";
    CALIBRE_LIBRARY = "${config.devenv.dotfile}/state/calibre";
    UV_CACHE_DIR = "${config.devenv.dotfile}/cache/uv";
    UV_PYTHON_DOWNLOADS = "never";
    UV_PYTHON = "${config.languages.python.package}/bin/python";
  };

  packages = [
    # Base packages
    pkgs.wget
    # Calibre
    pkgs.calibre
    # Utilities
    pkgs.go-task
  ];

  languages.python = {
    enable = true;
    package = pkgs.python311;
    uv.enable = true;
  };

  enterShell = ''
    uv venv --allow-existing
    source "$UV_PROJECT_ENVIRONMENT/bin/activate"
    ${pkgs.go-task.out}/bin/task install
  '';

  git-hooks = {
    hooks = {
      ruff.enable = true;
      ruff-format.enable = true;
      alejandra.enable = true;
      markdownlint.enable = true;
    };
  };

  devcontainer.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
