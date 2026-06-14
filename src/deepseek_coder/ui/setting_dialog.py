from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from deepseek_coder.infrastructure.deepseek_client import DeepSeekClient
from deepseek_coder.services.deepseek import DeepSeekManager
from deepseek_coder.services.settings import SettingsService

# Доступные темы qt-material
_THEMES = [
    "dark_teal.xml",
    "dark_blue.xml",
    "dark_purple.xml",
    "dark_red.xml",
    "dark_yellow.xml",
    "light_teal.xml",
]

_CODE_STYLES = [
    "monokai",
    "dracula",
    "one-dark",
    "github-dark",
    "nord",
    "gruvbox-dark",
    "solarized-dark",
    "friendly",
]


class SettingsDialog(QDialog):
    """Диалог настроек приложения.

    Позволяет пользователю настроить API ключ и выбрать модель.
    Поддерживает проверку соединения перед сохранением настроек.
    """

    def __init__(self, settings: SettingsService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(500)

        # Основной layout
        layout = QVBoxLayout(self)

        # Вкладки
        tabs = QTabWidget(parent=self)
        tabs.addTab(self._make_general_tab(), "Основные")
        tabs.addTab(self._make_appearance_tab(), "Внешний вид")
        tabs.addTab(self._make_mcp_tab(), "MCP серверы")
        layout.addWidget(tabs)

        # Кнопки Сохранить/Отмена - QDialogButtonBox
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )

        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _make_general_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)

        # API ключ с кнопкой показать/скрыть
        self._api_key_input = QLineEdit(parent=self)
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        if key := self._settings.get_api_key():
            self._api_key_input.setText(key)

        toggle_btn = QPushButton("👁", parent=self)
        toggle_btn.setCheckable(True)
        toggle_btn.setFixedWidth(32)
        toggle_btn.toggled.connect(
            lambda checked: self._api_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )

        api_layout = QHBoxLayout()
        api_layout.addWidget(self._api_key_input)
        api_layout.addWidget(toggle_btn)
        form.addRow("API-ключ:", api_layout)

        # Модель
        self._combo_model = QComboBox(parent=self)
        self._combo_model.addItems(["deepseek-v4-flash", "deepseek-v4-pro"])
        index = self._combo_model.findText(self._settings.get_model())
        if index >= 0:
            self._combo_model.setCurrentIndex(index)

        form.addRow("Модель", self._combo_model)

        # Проверка соединения
        self._check_btn = QPushButton("Проверить соединение", parent=widget)
        self._check_btn.clicked.connect(self.on_check_connect_clicked)
        form.addRow("", self._check_btn)

        # Системный промпт
        self._system_prompt_input = QTextEdit(parent=self)
        self._system_prompt_input.setPlaceholderText(
            "Системный промпт по умолчанию (необязательно)"
        )
        self._system_prompt_input.setMaximumHeight(100)
        self._system_prompt_input.setText(self._settings.get_system_prompt())
        form.addRow("Системный промпт", self._system_prompt_input)

        return widget

    def _make_appearance_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)

        # Тема приложения
        self._combo_theme = QComboBox(parent=widget)
        self._combo_theme.addItems(_THEMES)
        index = self._combo_theme.findText(self._settings.get_theme())
        if index >= 0:
            self._combo_theme.setCurrentIndex(index)
        form.addRow("Тема", self._combo_theme)

        # Стиль подстветки кода
        self._combo_code_style = QComboBox(parent=widget)
        self._combo_code_style.addItems(_CODE_STYLES)
        index = self._combo_code_style.findText(self._settings.get_code_style())
        if index >= 0:
            self._combo_code_style.setCurrentIndex(index)
        form.addRow("Стиль кода", self._combo_code_style)

        # Предупреждение что тема смениться после перезагрузки приложения
        note = QLabel("* Тема применится после перезапуска приложения")
        form.addRow("", note)

        return widget

    def _make_mcp_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Список сервер
        self._mcp_list = QListWidget(parent=widget)
        layout.addWidget(self._mcp_list)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self._add_server_btn = QPushButton("+ Добавить", parent=widget)
        self._remove_server_btn = QPushButton("✕ Удалить", parent=widget)
        btn_layout.addWidget(self._add_server_btn)
        btn_layout.addWidget(self._remove_server_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Форма для нового сервера
        form = QFormLayout()
        self._mcp_name = QLineEdit(parent=widget)
        self._mcp_command = QLineEdit(parent=widget)
        self._mcp_args = QLineEdit(parent=widget)
        self._mcp_args.setPlaceholderText("-y @modelcontextprotocol/server-filesystem /path")
        form.addRow("Имя:", self._mcp_name)
        form.addRow("Команда:", self._mcp_command)
        form.addRow("Аргументы:", self._mcp_args)
        layout.addLayout(form)

        # Загружаем существующие серверы
        self._load_mcp_list()

        # Сигналы
        self._add_server_btn.clicked.connect(self._on_add_mcp_server)
        self._remove_server_btn.clicked.connect(self._on_remove_mcp_server)
        return widget

    def _load_mcp_list(self) -> None:
        """Загрузить список серверов из настроек в QListWidget"""
        self._mcp_list.clear()
        for server in self._settings.get_mcp_servers():
            name = str(server.get("name", ""))
            command = str(server.get("command", ""))
            item = QListWidgetItem(f"{name} [{command}]")
            item.setData(Qt.ItemDataRole.UserRole, server)
            self._mcp_list.addItem(item)

    def _on_add_mcp_server(self) -> None:
        """Добавить новый сервер из полей формы."""
        name = self._mcp_name.text().strip()
        command = self._mcp_command.text().strip()
        args_text = self._mcp_args.text().strip()
        if not name or not command:
            return
        args = args_text.split() if args_text else []
        server = self._settings.get_mcp_servers()
        server.append({"name": name, "command": command, "args": args})
        self._settings.set_mcp_servers(server)
        self._load_mcp_list()
        # Очищаем форму
        self._mcp_name.clear()
        self._mcp_command.clear()
        self._mcp_args.clear()

    def _on_remove_mcp_server(self) -> None:
        """Удалить выбранный сервер."""
        item = self._mcp_list.currentItem()
        if item is None:
            return
        server_data = item.data(Qt.ItemDataRole.UserRole)
        name = server_data["name"]
        servers = self._settings.get_mcp_servers()
        update = [s for s in servers if s["name"] != name]
        self._settings.set_mcp_servers(update)
        self._load_mcp_list()

    def _on_save(self) -> None:
        self._settings.set_api_key(self._api_key_input.text())
        self._settings.set_model(self._combo_model.currentText())
        self._settings.set_system_prompt(self._system_prompt_input.toPlainText())
        self._settings.set_code_style(self._combo_code_style.currentText())
        self._settings.set_theme(self._combo_theme.currentText())
        self.accept()

    @asyncSlot() # type: ignore[untyped-decorator]
    async def on_check_connect_clicked(self) -> None:
        api_key = self._api_key_input.text()
        if not api_key:
            QMessageBox.warning(self, "Ошибка", "Отсутствует или не корректно введен API KEY")
            return
        model = self._combo_model.currentText()
        self._check_btn.setEnabled(False)
        self._check_btn.setText("Проверяю...")
        client = DeepSeekClient(api_key=api_key, model=model)
        manager = DeepSeekManager(client=client)
        try:
            text = await manager.chat("Reply with one word: OK")
            QMessageBox.information(self, "Успех", f"Ответ модели {text}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка соединения", str(exc))
        finally:
            self._check_btn.setText("Проверить соединение")
            self._check_btn.setEnabled(True)
