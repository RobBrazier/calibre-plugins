from calibre.customize import InterfaceActionBase

from ._version import __version_tuple__


class HardcoverSync(InterfaceActionBase):
    name = "Hardcover Sync"
    description = "Downloads metadata and covers from Hardcover.app"
    author = "Rob Brazier"
    version = __version_tuple__
    minimum_calibre_version = (7, 7, 0)

    actual_plugin = "calibre_plugins.hardcover_sync.action:HardcoverSyncAction"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with self:
            from .provider import HardcoverProvider

            self.provider = HardcoverProvider(self)

    def is_customizable(self):
        return True

    def config_widget(self):
        if self.actual_plugin_:
            print(self.actual_plugin_)
        return None
