import argparse
import ast
import logging
import os
import re
import subprocess
import tempfile
import zipfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def get_version(file: str) -> tuple[str, tuple]:
    with open(file, "r") as f:
        content = f.read()

    version_str = ast.literal_eval(content.split("__version__ = ")[1].split("\n")[0])
    version_tuple = ast.literal_eval(
        content.split("__version_tuple__ = ")[1].split("\n")[0]
    )

    return version_str, version_tuple


def download_dependencies(
    name: str, path: str, temp_dir: tempfile.TemporaryDirectory[str]
) -> list[str]:
    try:
        subprocess.run(
            [
                "uv",
                "--directory",
                path,
                "pip",
                "install",
                ".",
                "--target",
                temp_dir.name,
                "--link-mode",
                "copy",
            ]
        )
    except:
        logger.exception("Failed to install dependencies")
        raise

    dependencies: dict[str, str] = {}

    temp_path = temp_dir.name

    for file in os.listdir(temp_path):
        file_path = os.path.join(temp_path, file)
        dep_name = file

        if file.endswith("dist-info") or file == ".lock" or file == name:
            continue

        if file.endswith("pth"):
            with open(file_path) as f:
                file_path = f.read().strip()
                match = re.search(r"__editable__\.([^-]+)-", file)
                dep_name = match.group(1) if match else file
                module_path = os.path.join(file_path, dep_name)
                if os.path.exists(module_path):
                    file_path = module_path
                else:
                    logger.warning(
                        "couldn't match module name=%s, path=%s from file=%s",
                        dep_name,
                        module_path,
                        file,
                    )
                    continue
        dependencies[dep_name] = file_path

    return dependencies


def copy_to_zip(zf: zipfile.ZipFile, path: str, prefix=""):
    if os.path.isfile(path):
        zf.write(path, prefix)
        return

    for root, _, files in os.walk(path):
        for file in files:
            source_path = os.path.join(root, file)
            if "__pycache__" in source_path:
                continue
            target_path = os.path.join(prefix, os.path.relpath(source_path, path))
            zf.write(source_path, target_path)


def create_zip(
    plugin_name: str,
    plugin_path: str,
    outfile: str,
    dependencies: dict[str, str],
):
    with zipfile.ZipFile(outfile, "w", zipfile.ZIP_DEFLATED) as zf:
        copy_to_zip(zf, plugin_path)
        for dep_name, dep_path in dependencies.items():
            logger.info("Copying %s to %s", dep_path, dep_name)
            copy_to_zip(zf, dep_path, prefix=dep_name)

        zf.writestr(f"plugin-import-name-{plugin_name}.txt", "")


def main(args: argparse.Namespace):
    plugin_name = args.plugin_name
    plugin_package = plugin_name.replace("-", "_")
    plugin_dir = os.path.join(os.getcwd(), "plugins", plugin_name)
    pyproject_path = os.path.join(plugin_dir, "pyproject.toml")
    package_path = os.path.join(plugin_dir, "src", plugin_package)
    version_path = os.path.join(package_path, "_version.py")
    output_dir = os.path.join(os.getcwd(), "dist")

    if not os.path.exists(plugin_dir):
        raise ValueError(f"Plugin directory {plugin_dir} does not exist")

    if not os.path.exists(pyproject_path):
        raise ValueError(f"pyproject.toml not found at {pyproject_path}")

    if not os.path.exists(version_path):
        raise ValueError(f"No _version.py found at {version_path}")

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    version, version_tuple = get_version(version_path)
    output_file = os.path.join(output_dir, f"{plugin_name}-{version}.zip")

    temp_dir = tempfile.TemporaryDirectory()
    dependencies = download_dependencies(plugin_name, plugin_dir, temp_dir)

    create_zip(plugin_package, package_path, output_file, dependencies)

    logger.info(
        "Created bundle for %s version %s at %s", plugin_name, version, output_file
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("plugin_name", help="Plugin Name")

    main(parser.parse_args())
