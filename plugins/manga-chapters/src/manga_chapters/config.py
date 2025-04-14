from qt.core import QWidget, QVBoxLayout, QLabel, QLineEdit
from calibre.utils.config import JSONConfig

# Create a configuration
prefs = JSONConfig("plugins/manga_toc_generator")

# Set defaults
prefs.defaults["llm_endpoint"] = (
    "https://generativelanguage.googleapis.com/v1beta/openai/"
)
prefs.defaults["llm_model"] = "gemini-2.0-flash"
prefs.defaults["api_key"] = ""


class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # API Key
        self.layout.addWidget(QLabel("OpenAI-Compatible Endpoint:"))
        self.llm_endpoint = QLineEdit(self)
        self.llm_endpoint.setText(prefs["llm_endpoint"])
        self.layout.addWidget(self.llm_endpoint)
        self.layout.addWidget(QLabel("LLM Model Identifier:"))
        self.llm_model = QLineEdit(self)
        self.llm_model.setText(prefs["llm_model"])
        self.layout.addWidget(self.llm_model)
        self.layout.addWidget(QLabel("API Key"))
        self.api_key = QLineEdit(self)
        self.api_key.setText(prefs["api_key"])
        self.layout.addWidget(self.api_key)

        self.layout.addStretch(1)

    def save_settings(self):
        prefs["llm_endpoint"] = self.llm_endpoint.text().strip()
        prefs["llm_model"] = self.llm_model.text().strip()
        prefs["api_key"] = self.api_key.text().strip()
