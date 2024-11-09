import os
from typing import Any, Dict
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
import logging
import importlib
import inspect
import shutil

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CalibreBuildHook(BuildHookInterface):
    PLUGIN_NAME = "calibre"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        source_path = self.root

        deps_path = os.path.join(source_path, "src", "deps")

        included_deps = self.__get_dep_paths()
        for name, path in included_deps.items():
            dep_path = os.path.join(deps_path, name)
            os.makedirs(dep_path, exist_ok=True)
            shutil.copytree(path, dep_path, dirs_exist_ok=True)

    def finalize(
        self, version: str, build_data: dict[str, Any], artifact_path: str
    ) -> None:
        shutil.rmtree(os.path.join(self.root, "src", "deps"))

    def __get_dep_paths(self) -> Dict[str, str]:
        result = {}
        for name in self.config.get("include-deps", []):
            try:
                module = importlib.import_module(name)
                path = inspect.getfile(module)
                module_dir = os.path.dirname(path)
                module_name = os.path.basename(module_dir)
                result.update({module_name: module_dir})
            except Exception as e:
                logger.debug(f"failed to find {name} due to {e}")

        return result
