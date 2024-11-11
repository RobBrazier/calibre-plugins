import os
from typing import Any, Dict, List
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
import logging
import importlib
import inspect
import shutil
import sys

from pathlib import Path
import re

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def normalise_dependencies(deps: List[str]) -> List[str]:
    normalised = []
    for dep in deps:
        # remove whitespace around dependency
        dep = dep.strip()
        matches = re.split("([~=!<>])", dep, 2)
        if len(matches) > 0:
            normalised.append(matches[0].strip())
    return normalised


def get_project_dependencies(root: str) -> List[str]:
    pyproject_toml = Path(root) / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_toml.read_text(encoding="utf-8"))
    return normalise_dependencies(pyproject["project"]["dependencies"])


def get_project_name(root: str) -> List[str]:
    pyproject_toml = Path(root) / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_toml.read_text(encoding="utf-8"))
    return pyproject["project"]["name"]


class CalibreBuildHook(BuildHookInterface):
    PLUGIN_NAME = "calibre"

    def dependencies(self) -> list[str]:
        return ["tomli>=2.0.2; python_version < '3.11'"]

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        root_path = self.get_root_path()
        relative_root = self.get_root_path(relative=True)
        self.bundled_deps: List[str] = []

        included_deps = self.__get_dep_paths()
        for name, path in included_deps.items():
            self.bundled_deps.append(name)
            self.app.display_info(f"Bundling {name} into dist")
            dep_path = os.path.join(root_path, name)
            build_data["artifacts"].append(f"/{relative_root}/{name}")
            os.makedirs(dep_path, exist_ok=True)
            shutil.copytree(path, dep_path, dirs_exist_ok=True)

        open(os.path.join(root_path, self.get_import_filename()), "a").close()

    def finalize(
        self, version: str, build_data: dict[str, Any], artifact_path: str
    ) -> None:
        root_path = self.get_root_path()

        import_file = Path(os.path.join(root_path, self.get_import_filename()))
        if import_file.exists():
            import_file.unlink(True)

        if self.bundled_deps:
            for name in self.bundled_deps:
                dep_path = os.path.join(root_path, name)
                if os.path.exists(dep_path):
                    shutil.rmtree(dep_path)

    @staticmethod
    def __find_module(name):
        if virtualenv := os.getenv("UV_PROJECT_ENVIRONMENT"):
            sys.path.append(
                os.path.join(virtualenv, "lib", "python3.9", "site-packages")
            )
        # import from sys modules
        sys_module = sys.modules.get(name)
        if sys_module:
            return sys_module
        # import from loaded pythonpath
        try:
            module = importlib.import_module(name)
            return module
        except Exception:
            logger.exception(f"Unable to find module {name}")
        # import from VIRTUAL_ENV

    def get_import_filename(self) -> str:
        name = self.get_project_name()
        return f"plugin-import-name-{name}.txt"

    def get_dependencies(self) -> List[str]:
        deps = []
        project_deps = get_project_dependencies(self.root)
        included_deps = self.config.get("include-deps", [])
        deps.extend(project_deps)
        deps.extend(included_deps)

        return deps

    def get_project_name(self) -> str:
        project_name = get_project_name(self.root)
        project_name = self.config.get("import-name", project_name)
        return project_name

    def get_root_path(self, relative=False) -> str:
        root_path = self.config.get("root-path", "src")
        if relative:
            return root_path
        return os.path.join(self.root, root_path)

    def __get_dep_paths(self) -> Dict[str, str]:
        result = {}

        for name in self.get_dependencies():
            module = self.__find_module(name)
            if not module:
                continue
            path = inspect.getfile(module)
            module_dir = os.path.dirname(path)
            module_name = os.path.basename(module_dir)
            result.update({module_name: module_dir})

        return result
