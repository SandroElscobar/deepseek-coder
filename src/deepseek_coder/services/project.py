"""
Сервис для работы с проектами пользователя.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QFileSystemWatcher

logger = logging.getLogger(__name__)


@dataclass
class ProjectFile:
    path: Path
    relative_path: Path
    content: str
    truncated: bool = False


@dataclass
class ProjectContext:
    root_path: Path
    files: list[ProjectFile] = field(default_factory=list)
    total_files: int = 0
    skipped_files: int = 0

    def build_system_prompt(self) -> str:
        """Собрать системное сообщение из контекста."""
        lines = [f"Проект: {self.root_path.name}\n"]
        for f in self.files:
            lines.append(f"==={f.relative_path}===")
            lines.append(f.content)
            if f.truncated:
                lines.append("...[файл обрезан, используй read_file для полного содержимого]")
            lines.append("")
        return "\n".join(lines)


class ProjectManager:
    INCLUDED_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".json",
        ".md",
        ".yaml",
        ".yml",
        ".toml",
        ".html",
        ".css",
        ".txt",
        ".sh",
        ".env.example",
    }
    EXCLUDED_DIRS = {
        "node_modules",
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".mypy_cache",
        ".ruff_cache",
        "eggs",
        ".eggs",
    }

    MAX_FILE_SIZE = 50_000  # символов

    def __init__(self) -> None:
        self._context: ProjectContext | None = None
        self._watcher: QFileSystemWatcher | None = None

    def scan_project(self, root_path: str) -> ProjectContext:
        """Синхронное сканирование - запускать через asyncio.to_thread."""
        root = Path(root_path)
        context = ProjectContext(root_path=root)
        if not root.exists():
            raise FileNotFoundError(f"Директория не найдена: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Указанный путь не является директорией: {root}")
        logger.info("Сканирую проект: %s", root_path)
        for file_path in root.rglob("*"):
            if any(part in self.EXCLUDED_DIRS for part in file_path.parts):
                continue
            if not file_path.is_file():
                continue
            if file_path.suffix not in self.INCLUDED_EXTENSIONS:
                context.skipped_files += 1
                continue
            context.total_files += 1
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            truncated = False
            if len(content) > self.MAX_FILE_SIZE:
                content = content[: self.MAX_FILE_SIZE]
                truncated = True

            context.files.append(
                ProjectFile(
                    path=file_path,
                    relative_path=file_path.relative_to(root),
                    content=content,
                    truncated=truncated,
                ),
            )
        self._context = context
        logger.info("Сканирование завершено: %d файлов обработано", len(self._context.files))

        return context

    def get_system_prompt(self) -> str | None:
        """Получить текущий системный промпт или None если проект не открыт."""
        if self._context is None:
            return None
        return self._context.build_system_prompt()

    @property
    def current_root(self) -> Path | None:
        if self._context is None:
            return None
        return self._context.root_path
