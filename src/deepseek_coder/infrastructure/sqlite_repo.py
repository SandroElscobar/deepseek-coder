"""
Репозиторий чатов
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SessionInfo:
    id: int
    started_at: str
    preview: str


_CREATE_SESSIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

_CREATE_MESSAGES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

_CREATE_SESSION_SQL = """
INSERT INTO sessions DEFAULT VALUES
"""

_CREATE_MESSAGE_SQL = """
INSERT INTO messages (session_id, role, content)
VALUES (?, ?, ?);
"""

_GET_SESSION_MESSAGES_SQL = """
SELECT role, content FROM messages
WHERE session_id = ?
ORDER BY created_at ASC, id ASC
"""

_GET_LAST_SESSION_SQL = """
SELECT id FROM sessions
ORDER BY started_at DESC, id DESC
LIMIT 1
"""

_LIST_SESSIONS_SQL = """
SELECT
    s.id,
    s.started_at,
    (SELECT m.content FROM messages m
    WHERE m.session_id = s.id AND m.role = 'user'
    ORDER BY m.created_at ASC, m.id ASC
    LIMIT 1) AS preview
FROM sessions s
ORDER BY s.started_at DESC, s.id DESC
"""

_DELETE_SESSION_SQL = """
DELETE FROM sessions WHERE id = ?
"""


class ChatRepository:
    """Репозиторий для работы с историей чатов"""

    def __init__(self) -> None:
        self._conn: aiosqlite.Connection | None = None

    async def open(self, db_path: Path) -> None:
        """Открыть соединение и создать таблицы если не существуют."""
        self._conn = await aiosqlite.connect(db_path)
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._create_tables()

    async def _create_tables(self) -> None:
        """Создать все таблицы"""
        assert self._conn is not None
        await self._conn.execute(_CREATE_SESSIONS_TABLE_SQL)
        await self._conn.execute(_CREATE_MESSAGES_TABLE_SQL)
        await self._conn.commit()

    async def close(self) -> None:
        """Закрыть соединение с таблицей"""
        if self._conn is not None:
            try:
                await self._conn.close()
            except Exception:
                pass
            finally:
                self._conn = None

    async def create_session(self) -> int | None:
        """Создать новую сессию"""
        assert self._conn is not None
        async with self._conn.execute(_CREATE_SESSION_SQL) as cursor:
            await self._conn.commit()
            return cursor.lastrowid

    async def save_message(self, session_id: int, role: str, content: str) -> None:
        """Сохранить сообщение в сессии"""
        assert self._conn is not None
        await self._conn.execute(_CREATE_MESSAGE_SQL, (session_id, role, content))
        await self._conn.commit()

    async def load_session_message(self, session_id: int) -> list[tuple[str, str]]:
        """Загрузить сообщения сессии"""
        assert self._conn is not None
        if session_id <= 0:
            return []
        async with self._conn.execute(_GET_SESSION_MESSAGES_SQL, (session_id,)) as cursor:
            rows = await cursor.fetchall()
            return [(row[0], row[1]) for row in rows]

    async def load_last_session_id(self) -> int | None:
        """Загрузить последнюю сессии"""
        assert self._conn is not None
        async with self._conn.execute(_GET_LAST_SESSION_SQL) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return row[0]

    async def list_sessions(self) -> list[SessionInfo]:
        """Получить все сессии с превью первого user-сообщения."""
        assert self._conn is not None
        async with self._conn.execute(_LIST_SESSIONS_SQL) as cursor:
            rows = await cursor.fetchall()
            return [
                SessionInfo(id=row[0], started_at=row[1], preview=row[2] or "(Пустая сессия)")
                for row in rows
            ]

    async def delete_session(self, session_id: int) -> None:
        assert self._conn is not None
        await self._conn.execute(_DELETE_SESSION_SQL, (session_id,))
        await self._conn.commit()
