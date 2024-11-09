from calibre.utils.config import JSONConfig

try:
    from qt.core import QGridLayout, QLineEdit, QLabel, QWidget
except ImportError:
    from PyQt5.Qt import QGridLayout, QLineEdit, QLabel, QWidget

STORE_NAME = "Options"
API_KEY = "api_key"
DEFAULTS = {API_KEY: ""}


def init_prefs(name):
    prefs = JSONConfig(f"plugins/{name}")
    prefs.defaults = DEFAULTS
    return prefs


def get_option(prefs: JSONConfig, key: str):
    return prefs.get(key, DEFAULTS.get(key))


class APIConfigWidget(QWidget):
    def __init__(self, prefs: JSONConfig):
        QWidget.__init__(self)

        self.prefs = prefs

        self.layout = QGridLayout()
        self.layout.setSpacing(10)

        self.setLayout(self.layout)

        self.api_key = QLineEdit(self)
        self.api_key.setText(get_option(self.prefs, API_KEY))

        self.layout.addWidget(QLabel("API Key:"), 1, 0)
        self.layout.addWidget(self.api_key, 1, 1, 1, 20)

    def commit(self):
        new_prefs = {API_KEY: str(self.api_key.text()).strip()}

        self.prefs.update(new_prefs)
        self.prefs.commit()
