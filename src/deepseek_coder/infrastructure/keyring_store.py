"""
Обёртка над системным keychain для хранения секретов приложения.

Используется системное хранилище ОС:
  - macOS:   Keychain
  - Windows: Credential Manager
  - Linux:   Secret Service (GNOME Keyring / KWallet)
"""

import contextlib

import keyring
import keyring.errors

_SERVICE_NAME = "deepseek-coder"


class KeyringStore:
    """Типобезопасный интерфейс к системному keychain."""

    def save_api_key(self, api_key: str) -> None:
        keyring.set_password(_SERVICE_NAME, "api_key", api_key)

    def load_api_key(self) -> str | None:
        return keyring.get_password(_SERVICE_NAME, "api_key")

    def delete_api_key(self) -> None:
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(_SERVICE_NAME, "api_key")

    def has_api_key(self) -> bool:
        return keyring.get_password(_SERVICE_NAME, "api_key") is not None
