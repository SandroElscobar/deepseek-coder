from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QTextEdit, QWidget


class MessageInput(QTextEdit):
    """Многострочное поле ввода
    Enter        — сигнал submit_requested (отправить сообщение)
    Shift+Enter  — обычный перенос строки
    """

    # Сигнал без данных — данные получатель возьмёт сам через .toPlainText()
    submit_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Введите запрос... (Enter - отправить, Shift+Enter - новая строка")
        # Ограничим высоту: минимум 1 строка, максимум 5 строк
        self.setMinimumHeight(38)
        self.setMaximumHeight(120)
        # Убираем горизонтальный скролл, не нужен
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # Shift+Enter -> Обычный перенос строки (передаем в базовый класс)
        if event is None:
            return None
        if (
            event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ShiftModifier
        ):
            super().keyPressEvent(event)
            return None
        # Enter без модификаторов
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.submit_requested.emit()
            return None
        # Все остальное - стандартное поведение
        super().keyPressEvent(event)
        return None
