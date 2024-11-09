from hatchling.plugin import hookimpl

from .plugin import CalibreBuildHook


@hookimpl
def hatch_register_build_hook():
    return CalibreBuildHook
