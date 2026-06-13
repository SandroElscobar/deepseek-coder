from __future__ import annotations

import logging
from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QColor,
    QTextCharFormat,
    QTextCursor,
    QTextLength,
    QTextTableCellFormat,
    QTextTableFormat,
)
from PyQt6.QtWidgets import (
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from deepseek_coder.ui.markdown_renderer import markdown_to_html

logger = logging.getLogger(__name__)


@dataclass
class Message:
    role: str
    text: str


class ChatView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._browser = QTextBrowser(self)
        self._stream_buffer: str = ""
        self._browser.setOpenExternalLinks(True)

        self._stream_cursor: QTextCursor | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._browser)

    # --- Публичные API ---

    def _insert_message(self, role: str, text: str, as_markdown: bool = False) -> QTextCursor:
        """Вставляет сообщение в конец документа и возвращает курок внутри ячейки
        Курсор нужен для последующего дописывания текста при стриминге.
        Для уже завершённых сообщений возвращаемый курсор можно проигнорировать.
        """
        is_user = role == "user"
        is_tool = role == "tool"

        bubble_color = (
            QColor("#007968") if is_user else QColor("#1A237E") if is_tool else QColor("#263238")
        )
        text_color = QColor("#FFFFFF") if is_user else QColor("#ECEFF1")

        # 1. Готовим формат таблицы: ширина 70% документа, выравнивание, фон
        table_format = QTextTableFormat()
        table_format.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
        table_format.setAlignment(
            Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft
        )
        table_format.setBorder(0)
        table_format.setCellPadding(8)
        table_format.setCellSpacing(0)
        table_format.setBackground(bubble_color)
        table_format.setTopMargin(6)
        table_format.setBottomMargin(6)

        # Цвета пузырьков
        cell_format = QTextTableCellFormat()
        cell_format.setBackground(bubble_color)

        # 2. Готовим формат текста внутри: белый цвет, обычный размер
        char_format = QTextCharFormat()
        char_format.setForeground(text_color)

        # Получаем курсор в конце документа и вставляем в таблицу
        doc_cursor = self._browser.textCursor()
        doc_cursor.movePosition(QTextCursor.MoveOperation.End)
        table = doc_cursor.insertTable(1, 1, table_format)

        # Применяем cell_format к единственной ячейки
        cell = table.cellAt(0, 0)
        cell.setFormat(cell_format)

        # Берем курсор внутри ячейки он создается движком при вставке таблицы
        cell_cursor = table.cellAt(0, 0).firstCursorPosition()
        cell_cursor.setCharFormat(char_format)
        if text:
            if as_markdown and not is_user:
                cell_cursor.insertMarkdown(text)
                text_color = QColor("#ECEFF1")
                self._recolor_cell(cell, text_color)
            else:
                cell_cursor.insertText(text)

        return cell_cursor

    def add_user_message(self, text: str) -> None:
        """Добавляет завершенное сообщение пользователя."""
        self._insert_message("user", text)
        self._scroll_to_bottom()

    def start_assistant_message(self) -> None:
        """Открывает новое пустое сообщение ассистента и готовит курсор для стриминга."""
        self._stream_buffer = ""
        self._stream_cursor = self._insert_message("assistant", "")
        self._scroll_to_bottom()

    def append_to_last(self, chunk: str) -> None:
        """Дописываем чанк в текущее стримящееся сообщение."""
        if self._stream_cursor is None:
            logger.warning("append_to_last вызван без активного стрима")
            return None

        self._stream_buffer += chunk
        bar = self._browser.verticalScrollBar()
        was_at_bottom = bar.value() >= bar.maximum() - 4
        self._stream_cursor.insertText(chunk)
        if was_at_bottom:
            bar.setValue(bar.maximum())
        return None

    def stop_assistant_message(self) -> None:
        if self._stream_cursor is None:
            return None

        full_text = self._stream_buffer

        # Если буфер пустой — удаляем пустой пузырёк целиком
        if not full_text.strip():
            table = self._stream_cursor.currentTable()
            cursor = self._browser.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            # Выделяем и удаляем всю таблицу
            table.removeRows(0, table.rows())
            self._stream_cursor = None
            self._stream_buffer = ""
            return None

        # Обычный путь — рендерим markdown
        cell = self._stream_cursor.currentTable().cellAt(0, 0)
        start = cell.firstCursorPosition()
        end = cell.lastCursorPosition()
        clean_cursor = QTextCursor(start)
        clean_cursor.setPosition(end.position(), QTextCursor.MoveMode.KeepAnchor)
        clean_cursor.removeSelectedText()

        md_cursor = cell.firstCursorPosition()
        md_cursor.insertHtml(markdown_to_html(full_text))

        self._stream_cursor = None
        self._stream_buffer = ""
        self._scroll_to_bottom()
        return None

    def _scroll_to_bottom(self) -> None:
        bar = self._browser.verticalScrollBar()
        bar.setValue(bar.maximum())

    def clear(self) -> None:
        self._browser.clear()
        self._stream_cursor = None

    def load_history(self, messages: list[tuple[str, str]]) -> None:
        """Загружаем историю переписки"""
        self._browser.clear()
        self._stream_cursor = None
        self._stream_buffer = ""
        # Отключаем обновление виджета на время массовой вставки - заметно быстрее
        self._browser.setUpdatesEnabled(False)
        try:
            for role, text in messages:
                self._insert_message(role, text, as_markdown=True)
        finally:
            self._browser.setUpdatesEnabled(True)
        self._scroll_to_bottom()

    def _recolor_cell(self, cell, color: QColor) -> None:
        cursor = QTextCursor(cell.firstCursorPosition())
        cursor.setPosition(cell.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.mergeCharFormat(fmt)

    def add_tool_message(self, text: str) -> None:
        """Показать tool call как отдельное системное сообщение"""
        self._insert_message("tool", text)
        self._scroll_to_bottom()
