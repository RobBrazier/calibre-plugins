{ pkgs, lib, config, inputs, ... }:
{
  env.PYTHONPATH = "${config.devenv.dotfile}/profile/lib/calibre:${config.devenv.root}/src";
  env.CALIBRE_CONFIG_DIRECTORY = "${config.devenv.dotfile}/config/calibre";
  env.CALIBRE_TEMP_DIR = "${config.devenv.dotfile}/temp/calibre";
  env.CALIBRE_NO_DEFAULT_PROGRAMS = "1";
  env.CALIBRE_LIBRARY = "${config.devenv.dotfile}/state/calibre";
  env.UV_CACHE_DIR = "${config.devenv.dotfile}/cache/uv";

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
  languages.python = {
    enable = true;
    # package = pkgs.python39;
    uv.enable = true;
    uv.sync.enable = true;
    venv.enable = true;
  };

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.setup-calibre.exec = ''
    books="1513.epub.noimages"

    # download books - separated by newline
    echo "$books" | xargs -I {} wget -P "$CALIBRE_TEMP_DIR" --no-clobber --content-disposition "https://www.gutenberg.org/ebooks/{}"

    # import books
    find "$CALIBRE_TEMP_DIR" -name "*.epub" | xargs -I {} sh -c 'calibredb add --with-library "$CALIBRE_LIBRARY" "{}" && rm "{}"'

    calibre --with-library $CALIBRE_LIBRARY
  '';
  scripts.package.exec = ''
    (cd "${config.devenv.root}/plugins/$1" && uvx hatch build -t zipped-directory)
  '';
  scripts.install-plugin.exec = ''
    find "${config.devenv.root}/plugins/$1/dist" -name '*.zip' -type f | xargs calibre-customize --add-plugin
  '';
  scripts.run-hardcover.exec = ''
    package 'hardcover' && install-plugin 'hardcover'
    calibre-debug -r Hardcover -- "$@"
  '';
  scripts.hatch.exec = ''
    uvx hatch -- "$@"
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
