import os
from typing import Any, Dict, List
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
import logging
import importlib
import inspect
import glob
import sys
import tempfile

from pathlib import Path
import re

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CalibreBuildHook(BuildHookInterface):
    PLUGIN_NAME = "calibre"

    temp_file: Any

    def dependencies(self) -> list[str]:
        return ["tomli>=2.0.2; python_version < '3.11'"]

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        relative_root = self.get_root_path(relative=True)

        self.enhance_pythonpath()

        # Bundle dependencies into artifact
        included_deps = self.__get_dep_paths()
        for name, path in included_deps.items():
            self.app.display_info(f"Bundling {name} into dist")
            build_data["force_include"].update(
                {path: os.path.join(relative_root, name)}
            )
        name = self.get_project_name()

        # Create calibre plugin import file
        self.temp_file = tempfile.NamedTemporaryFile()
        build_data["force_include"].update(
            {
                self.temp_file.name: os.path.join(
                    relative_root, f"plugin-import-name-{name}.txt"
                )
            }
        )

    def finalize(
        self, version: str, build_data: dict[str, Any], artifact_path: str
    ) -> None:
        if self.temp_file:
            self.temp_file.close()

    def get_project_name(self) -> List[str]:
        pyproject_toml = Path(self.root) / "pyproject.toml"
        pyproject = tomllib.loads(pyproject_toml.read_text(encoding="utf-8"))
        return pyproject["project"]["name"]

    def get_project_dependencies(self) -> List[str]:
        pyproject_toml = Path(self.root) / "pyproject.toml"
        pyproject = tomllib.loads(pyproject_toml.read_text(encoding="utf-8"))
        return self.normalise_dependencies(pyproject["project"]["dependencies"])

    @staticmethod
    def normalise_dependencies(deps: List[str]) -> List[str]:
        normalised = []
        for dep in deps:
            # remove whitespace around dependency
            dep = dep.strip()
            matches = re.split("([~=!<>])", dep, 2)
            if len(matches) > 0:
                normalised.append(matches[0].strip())
        return normalised

    def enhance_pythonpath(self):
        if virtualenv := os.getenv("UV_PROJECT_ENVIRONMENT"):
            paths = glob.glob(
                os.path.join(virtualenv, "**", "site-packages"), recursive=True
            )
            sys.path.extend(paths)

        base_path = self.get_base_path()

        for path in self.config.get("local-libs", []):
            if not str(path).startswith(os.sep):
                path = os.path.normpath(os.path.join(base_path, path))
            sys.path.append(path)

    @staticmethod
    def __find_module(name):
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

    def get_dependencies(self) -> List[str]:
        deps = []
        project_deps = self.get_project_dependencies()
        deps.extend(project_deps)

        return deps

    def get_root_path(self, relative=False) -> str:
        root_path = self.config.get("root-path", "src")
        if relative:
            return root_path
        return os.path.join(self.root, root_path)

    def get_base_path(self) -> str:
        base_path = self.config.get("base-path", ".")
        return os.path.join(self.root, base_path)

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
