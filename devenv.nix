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
    pkgs.wget
    # Calibre
    pkgs.calibre
  ];

  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    version = "3.9";
    uv.enable = true;
  };

  scripts.setup-calibre.exec = ''
    books="1513.epub.noimages"

    # download books - separated by newline
    echo "$books" | xargs -I {} wget -P "$CALIBRE_TEMP_DIR" --no-clobber --content-disposition "https://www.gutenberg.org/ebooks/{}"

    # import books
    find "$CALIBRE_TEMP_DIR" -name "*.epub" | xargs -I {} sh -c 'calibredb add --with-library "$CALIBRE_LIBRARY" "{}" && rm "{}"'

    calibre --with-library $CALIBRE_LIBRARY
  '';
  scripts.package.exec = ''
    uv --directory "${config.devenv.root}/plugins/$1" run hatch build -t zipped-directory
  '';
  scripts.plugin-install.exec = ''
    find "${config.devenv.root}/plugins/$1/dist" -name '*.zip' -type f | xargs calibre-customize --add-plugin
  '';
  scripts.hardcover-install.exec = ''
    package 'hardcover' && plugin-install 'hardcover'
  '';
  scripts.hardcover-run.exec = ''
    hardcover-install
    calibre-debug -r Hardcover -- "$@"
  '';
  #
  enterShell = ''
    uv venv --allow-existing
    source "${config.devenv.dotfile}/state/venv/bin/activate"
    uv sync --all-packages
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
