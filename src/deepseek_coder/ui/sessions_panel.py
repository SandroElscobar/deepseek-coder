from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QContextMenuEvent
from PyQt6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from deepseek_coder.infrastructure.sqlite_repo import SessionInfo


class SessionsPanel(QWidget):
    """Боковая панель: список сессий, кнопка нового чата, удаление."""

    session_selected = pyqtSignal(int)
    session_deleted = pyqtSignal(int)
    new_chat_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._new_chat_btn = QPushButton("+ Новый чат", parent=self)
        self._list = QListWidget(parent=self)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("История", parent=self))
        layout.addWidget(self._new_chat_btn)
        layout.addWidget(self._list)

        self._new_chat_btn.clicked.connect(self.new_chat_requested)
        self._list.itemClicked.connect(self._on_item_clicked)

        self.setFixedWidth(220)

    def load_sessions(self, sessions: list[SessionInfo]) -> None:
        """Очистить список и заполнить заново"""
        self._list.clear()
        for session in sessions:
            date = session.started_at[:10]
            preview = session.preview[:40]
            text = f"{date}\n{preview}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, session.id)
            self._list.addItem(item)

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        """Контекстное меню по правой кнопке - удаление сессии."""
        if event is None:
            return None
        viewport = self._list.viewport()
        if viewport is None:
            return None
        item = self._list.itemAt(viewport.mapFromGlobal(event.globalPos()))
        if item is None:
            return None
        menu = QMenu(self)
        deleted_action = menu.addAction("🗑 Удалить")
        chosen = menu.exec(event.globalPos())
        if chosen == deleted_action:
            reply = QMessageBox.question(
                self, "Удалить диалог", "Удалить этот диалог? Это действие нельзя отменить!"
            )
            if reply == QMessageBox.StandardButton.Yes:
                session_id = item.data(Qt.ItemDataRole.UserRole)
                row = self._list.row(item)
                self._list.takeItem(row)
                self.session_deleted.emit(session_id)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        session_id = item.data(Qt.ItemDataRole.UserRole)
        self.session_selected.emit(session_id)
