from PySide6.QtCore import QSettings

from config import DEFAULT_API_TOKEN, DEFAULT_API_URL


class ClientSettings:
    """Persistent settings for the Windows client."""

    ORGANIZATION = "RPiRouter"
    APPLICATION = "RPiRouterControl"

    def __init__(self, backend=None):
        self._settings = backend or QSettings(
            self.ORGANIZATION,
            self.APPLICATION,
        )

    def api_url(self):
        return str(
            self._settings.value("connection/api_url", DEFAULT_API_URL)
        ).strip()

    def api_token(self):
        return str(
            self._settings.value("connection/api_token", DEFAULT_API_TOKEN)
        ).strip()

    def save_connection(self, api_url, api_token):
        self._settings.setValue("connection/api_url", api_url.strip())
        self._settings.setValue("connection/api_token", api_token.strip())
        self._settings.sync()
