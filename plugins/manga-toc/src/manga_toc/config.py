from qt.core import QWidget, QVBoxLayout, QLabel, QLineEdit
from calibre.utils.config import JSONConfig

# Create a configuration
prefs = JSONConfig("plugins/manga_toc_generator")

# Set defaults
prefs.defaults["api_key"] = ""


class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # API Key
        self.layout.addWidget(QLabel("Gemini API Key:"))
        self.api_key = QLineEdit(self)
        self.api_key.setText(prefs["api_key"])
        self.layout.addWidget(self.api_key)

        self.layout.addStretch(1)

    def save_settings(self):
        prefs["api_key"] = self.api_key.text().strip()
