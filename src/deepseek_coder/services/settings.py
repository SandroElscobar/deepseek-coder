"""
Сервис настроек приложения.
...
"""

import json
import logging

from PyQt6.QtCore import QSettings, QByteArray

from deepseek_coder.infrastructure.keyring_store import KeyringStore

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "deepseek-v4-flash"


class SettingsService:
    """Централизованный доступ к настройкам: API-ключ через keyring, остальное через QSettings."""

    def __init__(self, keyring: KeyringStore) -> None:
        self._keyring = keyring
        self._settings = QSettings("DeepSeekCoder", "App")

    def get_api_key(self) -> str | None:
        return self._keyring.load_api_key()

    def set_api_key(self, api_key: str) -> None:
        self._keyring.save_api_key(api_key)

    def get_model(self) -> str:
        return str(self._settings.value("model", defaultValue="deepseek-v4-flash"))

    def set_model(self, model: str) -> None:
        self._settings.setValue("model", model)

    def get_theme(self) -> str:
        return str(self._settings.value("theme", defaultValue="dark_teal.xml"))

    def set_theme(self, theme: str) -> None:
        self._settings.setValue("theme", theme)

    def get_code_style(self) -> str:
        return str(self._settings.value("code_style", defaultValue="monokai"))

    def set_code_style(self, style: str) -> None:
        self._settings.setValue("code_style", style)

    # Новый системный промпт
    def get_system_prompt(self) -> str:
        return str(self._settings.value("system_prompt", defaultValue=""))

    def set_system_prompt(self, prompt: str) -> None:
        self._settings.setValue("system_prompt", prompt)

    def get_mcp_servers(self) -> list[dict[str, object]]:
        raw = str(self._settings.value("mcp_servers", defaultValue="[]"))
        return json.loads(raw) if raw else []

    def set_mcp_servers(self, servers: list[dict[str, object]]) -> None:
        self._settings.setValue("mcp_servers", json.dumps(servers))

    def get_window_geometry(self) -> QByteArray | bytes | bytearray:
        return self._settings.value("window_geometry", defaultValue=None)

    def set_window_geometry(self, geometry: QByteArray) -> None:
        self._settings.setValue("window_geometry", geometry)

    def get_splitter_state(self, name: str) -> QByteArray | None:
        return self._settings.value(f"splitter_{name}", defaultValue=None)

    def set_splitter_state(self, name: str, state: QByteArray) -> None:
        self._settings.setValue(f"splitter_{name}", state)


