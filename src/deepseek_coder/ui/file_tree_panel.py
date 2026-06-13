"""Панель файлового дерева проекта с просмотром содержимого"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QModelIndex, QSortFilterProxyModel, pyqtSignal
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QLabel, QTreeView, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class FileTreeFilter(QSortFilterProxyModel):
    """Скрывает служебные директории из дерева файлов."""

    EXCLUDE_DIRS = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".eggs",
        ".idea",
        ".vscode",
    }

    def filterAcceptsRow(self, row: int, parent: QModelIndex) -> bool:
        source_model = self.sourceModel()
        if source_model is None:
            return False
        index = source_model.index(row, 0, parent)
        file_name = source_model.data(index, QFileSystemModel.Roles.FileNameRole)
        if file_name is None:
            return True
        return file_name not in self.EXCLUDE_DIRS


class FileTreePanel(QWidget):
    """Дерево файлов проетка"""

    file_selected = pyqtSignal(Path)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._label = QLabel("Проект не открыт", parent=self)

        # Модель файловой системы
        self._fs_model = QFileSystemModel(parent=self)
        self._fs_model.setRootPath("")

        # Фильтр поверх модели
        self._proxy = FileTreeFilter(parent=self)
        self._proxy.setSourceModel(self._fs_model)
        self._proxy.setFilterKeyColumn(0)
        self._proxy.setRecursiveFilteringEnabled(True)

        # Дерево
        self._tree = QTreeView(parent=self)
        self._tree.setModel(self._proxy)
        self._tree.hideColumn(1)
        self._tree.hideColumn(2)
        self._tree.hideColumn(3)

        self._tree.clicked.connect(self._on_item_clicked)

        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(self._tree)

    def set_root(self, path: Path) -> None:
        """Установить корневую директорию проекта."""
        root_index = self._fs_model.setRootPath(str(path))
        proxy_index = self._proxy.mapFromSource(root_index)
        self._tree.setRootIndex(proxy_index)
        self._label.setText(f"📁 {path.name}")

    def _on_item_clicked(self, proxy_index: QModelIndex) -> None:
        source_index = self._proxy.mapToSource(proxy_index)
        if not self._fs_model.isDir(source_index):
            path = self._fs_model.filePath(source_index)
            self.file_selected.emit(Path(path))
