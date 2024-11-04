{ pkgs, lib, config, inputs, ... }:
let
  pkgs-unstable = import inputs.nixpkgs-unstable { system = pkgs.stdenv.system; };
in
{
  env.PYTHONPATH = "${config.devenv.dotfile}/profile/lib/calibre:${config.devenv.root}/src";
  env.CALIBRE_CONFIG_DIRECTORY = "${config.devenv.dotfile}/config/calibre";
  env.CALIBRE_TEMP_DIR = "${config.devenv.dotfile}/temp/calibre";
  env.CALIBRE_NO_DEFAULT_PROGRAMS = "1";
  env.CALIBRE_LIBRARY = "${config.devenv.dotfile}/state/calibre";

  # https://devenv.sh/packages/
  packages = [
    # Base packages
    pkgs.git
    pkgs.wget
    pkgs.bash
    # Calibre
    pkgs.calibre
  ];

  # https://devenv.sh/languages/
  languages.python.enable = true;
  # languages.python.libraries = [
  #   "${config.devenv.root}/calibre/src"
  # ];
  languages.python.poetry.enable = true;
  languages.python.poetry.activate.enable = true;
  languages.python.poetry.install.enable = true;

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.setup-calibre.exec = ''
    bash ${config.devenv.root}/scripts/init_library.sh
    calibre --with-library $CALIBRE_LIBRARY
  '';
  scripts.package.exec = ''
    bash ${config.devenv.root}/scripts/package_plugins.sh
  '';
  scripts.install-plugins.exec = ''
    find dist -name '*.zip' -type f | xargs calibre-customize --add-plugin
  '';
  scripts.run-hardcover.exec = ''
    package && install-plugins
    calibre-debug -r Hardcover -- "$@"
  '';
  #
  # enterShell = ''
  #   hello
  #   git --version
  # '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  # enterTest = ''
  #   echo "Running tests"
  #   git --version | grep --color=auto "${pkgs.git.version}"
  # '';

  # https://devenv.sh/pre-commit-hooks/
  pre-commit.hooks = {
    ruff.enable = true;
    ruff-format.enable = true;
    shellcheck.enable = true;
  };

  # See full reference at https://devenv.sh/reference/options/
}
