from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from deepseek_coder.ui.markdown_renderer import _code_style


class FileViewer(QWidget):
    """Панель просмотра файла - только чтение"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._label = QLabel("Файл не выбран", parent=self)
        self._editor = QTextBrowser(parent=self)
        self._editor.setReadOnly(True)
        self._editor.setOpenExternalLinks(False)

        # Моноширинный шрифт через QFont
        # font = QFont("Consolas")
        # font.setStyleHint(QFont.StyleHint.Monospace)
        # self._editor.setFont(font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        layout.addWidget(self._editor)

        self.hide()

    def show_file(self, path: Path) -> None:
        """Загрузить и показать файл."""
        content = path.read_text(encoding="utf-8", errors="ignore")
        self._editor.setHtml(self._highlight(path, content))
        self._label.setText(path.name)
        self.show()

    def clear(self) -> None:
        """Скрыть панель"""
        self._editor.clear()
        self.hide()

    @staticmethod
    def _highlight(path: Path, content: str) -> str:
        """Подсветка синтаксиса через Pygments."""
        try:
            from pygments.lexers import get_lexer_for_filename
            from pygments.util import ClassNotFound

            try:
                lexer = get_lexer_for_filename(path.name)
            except ClassNotFound:
                from pygments.lexers import TextLexer

                lexer = TextLexer()
            from pygments import highlight
            from pygments.formatters import HtmlFormatter

            formatter = HtmlFormatter(noclasses=True, style=_code_style, full=True)
            return highlight(content, lexer, formatter)
        except Exception:
            return f"<pre>{content}</pre>"
