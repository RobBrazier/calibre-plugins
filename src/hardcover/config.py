from calibre.utils.config import JSONConfig

try:
    from qt.core import QGridLayout, QLineEdit, QLabel, QWidget
except ImportError:
    from PyQt5.Qt import QGridLayout, QLineEdit, QLabel, QWidget

plugin_prefs = JSONConfig("plugins/hardcover")
STORE_NAME = "Options"
API_KEY = "api_key"
DEFAULTS = {API_KEY: ""}
plugin_prefs.defaults[STORE_NAME] = DEFAULTS


def get_option(key):
    return plugin_prefs[STORE_NAME].get(key, DEFAULTS.get(key))


class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.layout = QGridLayout()
        self.layout.setSpacing(10)

        self.setLayout(self.layout)

        self.api_key = QLineEdit(self)
        self.api_key.setText(get_option(API_KEY))

        self.layout.addWidget(QLabel("API Key:"), 1, 0)
        self.layout.addWidget(self.api_key, 1, 1, 1, 20)

    def commit(self):
        new_prefs = {API_KEY: str(self.api_key.text()).strip()}

        plugin_prefs[STORE_NAME] = new_prefs
