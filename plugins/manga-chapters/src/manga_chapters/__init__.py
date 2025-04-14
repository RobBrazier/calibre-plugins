from calibre.customize import EditBookToolPlugin

from ._version import __version_tuple__


class MangaTocPlugin(EditBookToolPlugin):
    name = "Manga ToC Plugin"
    description = "An Editor Plugin (using Gemini GenAI) to extract Chapters from the Contents image in manga epubs"
    version = __version_tuple__
    author = "Rob Brazier"
    supported_platforms = ["windows", "osx", "linux"]
    minimum_calibre_version = (7, 7, 0)

    def config_widget(self):
        from .config import ConfigWidget

        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()

    def is_customizable(self):
        return True
