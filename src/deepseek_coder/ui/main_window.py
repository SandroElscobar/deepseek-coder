"""
Главное окно приложения.
"""

import asyncio
import contextlib
import logging
from pathlib import Path

from PyQt6.QtCore import QFileSystemWatcher, Qt
from PyQt6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncClose, asyncSlot

from deepseek_coder import ChatRepository, MCPManager
from deepseek_coder.services.agents import AGENTS, get_agent
from deepseek_coder.services.deepseek import TOOL_CALL_PREFIX, DeepSeekManager
from deepseek_coder.services.history import ChatHistoryService
from deepseek_coder.services.project import ProjectManager
from deepseek_coder.services.settings import SettingsService
from deepseek_coder.ui.chat_view import ChatView
from deepseek_coder.ui.file_tree_panel import FileTreePanel
from deepseek_coder.ui.file_viewer import FileViewer
from deepseek_coder.ui.message_input import MessageInput
from deepseek_coder.ui.sessions_panel import SessionsPanel
from deepseek_coder.ui.setting_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class MainWindow(QWidget):
    """Минимальное окно для проверки работоспособности Qt."""

    def __init__(
        self,
        manager: DeepSeekManager,
        settings: SettingsService,
        project_manager: ProjectManager,
        history_service: ChatHistoryService,
        repo: ChatRepository,
        mcp_manager: MCPManager,
    ) -> None:
        super().__init__()
        # Открытие настроек для API KEY
        shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        self._current_task: asyncio.Task | None = None
        self._watcher = QFileSystemWatcher(parent=self)
        self._watcher.fileChanged.connect(self.on_file_changed)
        self._manager = manager
        self._project_manager = project_manager
        self._settings = settings
        self._history_service = history_service
        self._file_tree = FileTreePanel(parent=self)
        self._file_viewer = FileViewer(parent=self)
        self._repo = repo
        self._mcp_manager = mcp_manager

        # Виджеты
        self._session_panel = SessionsPanel(parent=self)
        self._chat_view = ChatView(parent=self)

        # После для ввода промпта
        self._input_message = MessageInput(parent=self)
        self._submit = QPushButton("Отправить", parent=self)
        # Подключаем оба способа отправки - кнопка + Enter
        self._input_message.setPlaceholderText("Введите запрос")
        self._input_message.submit_requested.connect(self.on_submit_clicked)
        self._submit.clicked.connect(self.on_submit_clicked)

        # Layout'ы
        main_layout = QVBoxLayout(self)

        # Layout and Button для выбора Project для анализа
        tool_bar_layout = QHBoxLayout()
        self._open_project_btn = QPushButton("📁 Открыть проект", parent=self)
        self._project_label = QLabel("Проект не открыт", parent=self)
        self._agent_combo = QComboBox(parent=self)
        for agent in AGENTS.values():
            self._agent_combo.addItem(f"{agent.icon} {agent.display_name}", agent.name)
        self._agent_combo.currentIndexChanged.connect(self._on_agent_changed)
        tool_bar_layout.addWidget(self._agent_combo)
        tool_bar_layout.addWidget(self._open_project_btn)
        tool_bar_layout.addWidget(self._project_label)
        tool_bar_layout.addStretch()
        self._open_project_btn.clicked.connect(self.on_open_project_clicked)
        main_layout.addLayout(tool_bar_layout)

        # Левая колонка
        self._left_splitter = QSplitter(Qt.Orientation.Vertical, parent=self)
        self._left_splitter.addWidget(self._session_panel)
        self._left_splitter.addWidget(self._file_tree)
        self._left_splitter.setSizes([300, 300])

        # Главный сплиттер
        self._splitter = QSplitter(Qt.Orientation.Horizontal, parent=self)
        self._splitter.addWidget(self._left_splitter)
        self._splitter.addWidget(self._chat_view)
        self._splitter.addWidget(self._file_viewer)
        self._splitter.setSizes([220, 500, 300])
        main_layout.addWidget(self._splitter, stretch=1)

        # Поле ввода внизу
        input_layout = QHBoxLayout()
        input_layout.addWidget(self._input_message)
        input_layout.addWidget(self._submit)

        main_layout.addLayout(input_layout)

        # Сигналы для session_panel
        self._session_panel.session_selected.connect(self.on_session_selected)
        self._session_panel.session_deleted.connect(self.on_session_deleted)
        self._session_panel.new_chat_requested.connect(self.on_new_chat_clicked)

        shortcut.activated.connect(self.on_open_settings)

        # Параметры окна
        self.setWindowTitle("DeepSeek Coder")
        self.resize(900, 650)

        # Сигналы для _file_tree
        self._file_tree.file_selected.connect(self._on_file_selected)
        self._restore_window_state()

    @asyncSlot()
    async def on_submit_clicked(self) -> None:
        """Создает Task и переключает кнопку"""
        text = self._input_message.toPlainText().strip()
        if not text:
            return
        self._current_task = asyncio.create_task(self._run_chat(text))
        self._submit.setText("⏹ Стоп")
        self._submit.clicked.disconnect()
        self._submit.clicked.connect(self._cancel_current_task)
        try:
            await self._current_task
        except asyncio.CancelledError:
            self._chat_view.stop_assistant_message()
            self._chat_view.append_to_last("\n[Отменено]")
        finally:
            self._submit.setText("Отправить")
            self._submit.clicked.disconnect()
            self._submit.clicked.connect(self.on_submit_clicked)
            self._current_task = None


    async def _run_chat(self, text: str) -> None:
        """Вся логика отправки сообщения"""
        session_before = self._history_service.session_id
        self._input_message.setEnabled(False)
        self._input_message.clear()
        self._chat_view.add_user_message(text)
        self._chat_view.start_assistant_message()

        try:
            async for chunk in self._manager.chat_auto(text):
                if chunk.startswith(TOOL_CALL_PREFIX):
                    tool_text = chunk[len(TOOL_CALL_PREFIX) :]
                    self._chat_view.stop_assistant_message()
                    self._chat_view.add_tool_message(tool_text)
                    self._chat_view.start_assistant_message()
                else:
                    self._chat_view.append_to_last(chunk)
        except Exception as exc:
            self._chat_view.append_to_last(f"\n[Ошибка: {exc}]")
            logger.exception("Ошибка chat_stream")
        finally:
            is_new_session = session_before is None and self._history_service.session_id is not None
            self._chat_view.stop_assistant_message()
            self._input_message.setEnabled(True)
            if is_new_session:
                await self._refresh_sessions()

    def _cancel_current_task(self) -> None:
        if self._current_task is not None:
            self._current_task.cancel()

    @asyncSlot()
    async def on_open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, parent=self)
        closed = asyncio.Event()
        dialog.finished.connect(lambda _: closed.set())
        dialog.open()
        logger.info("Настройки открыты.")
        await closed.wait()
        logger.info("Настройки закрыты.")

    @asyncSlot()
    async def on_open_project_clicked(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Открыть проект")
        if not path:
            return
        self._open_project_btn.setEnabled(False)
        self._project_label.setText("Сканирую...")
        try:
            context = await asyncio.to_thread(self._project_manager.scan_project, path)
            self._file_tree.set_root(Path(path))
            self._watcher.addPaths([str(f.path) for f in context.files])
            current_index = self._agent_combo.currentIndex()
            self._on_agent_changed(current_index)
            self._project_label.setText(
                f"📁 {context.root_path.name} | файлов: {context.total_files}"
            )
        except Exception as exc:
            self._project_label.setText(f"Ошибка: {exc}")
        finally:
            self._open_project_btn.setEnabled(True)

    @asyncSlot()
    async def on_new_chat_clicked(self) -> None:
        await self._manager.new_chat()
        self._chat_view.clear()

    @asyncSlot(str)
    async def on_file_changed(self, path: str) -> None:
        """Файл изменился - сканируем проект."""
        self._watcher.addPath(path)
        if self._project_manager.current_root is None:
            return
        try:
            await asyncio.to_thread(
                self._project_manager.scan_project, str(self._project_manager.current_root)
            )
            self._manager.set_system_context(
                self._build_system_prompt(self._agent_combo.currentIndex())
            )
        except Exception as exc:
            logger.error("Ошибка обновления контекста: %s", exc)

    @asyncSlot(int)
    async def on_session_selected(self, session_id: int) -> None:
        """Пользователь выбрал сессию в боковой панели"""
        self._submit.setEnabled(False)
        try:
            messages = await self._history_service.switch_session(session_id)
            self._manager.load_history(messages)
            self._chat_view.load_history(messages)
        finally:
            self._submit.setEnabled(True)

    @asyncSlot(int)
    async def on_session_deleted(self, session_id: int) -> None:
        """Пользователь удалил сессию"""
        is_current = session_id == self._history_service.session_id
        await self._history_service.delete_session(session_id)
        if is_current:
            self._chat_view.clear()
        await self._refresh_sessions()

    async def initialize(self) -> None:
        """Загрузить начальное состояние после показа окна."""
        await self._refresh_sessions()

    async def _refresh_sessions(self) -> None:
        """Обновить список сессий в боковой панели."""
        sessions = await self._history_service.list_sessions()
        self._session_panel.load_sessions(sessions)

    def load_history(self, messages: list[tuple[str, str]]) -> None:
        self._chat_view.load_history(messages)

    def _set_input_enabled(self, enabled: bool) -> None:
        self._input_message.setEnabled(enabled)
        self._submit.setEnabled(enabled)

    def _on_file_selected(self, path: Path) -> None:
        self._file_viewer.show_file(path)

    def _on_agent_changed(self, index: int) -> None:
        """Пользователь выбрал агента - обновляем system prompt"""
        self._manager.set_system_context(self._build_system_prompt(index))

    def _build_system_prompt(self, index: int) -> str | None:
        user_system_prompt = self._settings.get_system_prompt()
        agent_name = self._agent_combo.itemData(index)
        agent = get_agent(agent_name)
        agent_system_prompt = agent.system_prompt
        project_system_prompt = self._project_manager.get_system_prompt()
        parts = [
            prompt
            for prompt in [user_system_prompt, agent_system_prompt, project_system_prompt]
            if prompt
        ]  # noqa: E501
        return "\n\n".join(parts) or None

    @asyncClose
    async def closeEvent(self, event: QCloseEvent) -> None:
        self._save_window_state()
        with contextlib.suppress(Exception):
            await self._mcp_manager.stop_all()
        with contextlib.suppress(Exception):
            await self._repo.close()

    def _save_window_state(self) -> None:
        self._settings.set_window_geometry(self.saveGeometry())
        self._settings.set_splitter_state("main", self._splitter.saveState())
        self._settings.set_splitter_state("left", self._left_splitter.saveState())

    def _restore_window_state(self) -> None:
        if geometry := self._settings.get_window_geometry():
            self.restoreGeometry(geometry)
        if state := self._settings.get_splitter_state("main"):
            self._splitter.restoreState(state)
        if state := self._settings.get_splitter_state("left"):
            self._left_splitter.restoreState(state)
