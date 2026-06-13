"""Сервис для работы с репозиторием чатов"""

import logging

from deepseek_coder.infrastructure.sqlite_repo import ChatRepository, SessionInfo

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """Сервис истории чатов"""

    def __init__(self, repo: ChatRepository) -> None:
        self._session_id: int | None = None
        self._repo = repo

    async def start_new_session(self) -> None:
        """Создать новую сессию"""
        self._session_id = None

    async def restore_last_session(self) -> list[tuple[str, str]]:
        """Загрузить сообщения последней сессии"""
        session_id = await self._repo.load_last_session_id()
        if session_id is not None:
            self._session_id = session_id
            return await self._repo.load_session_message(session_id=self._session_id)
        else:
            await self.start_new_session()
        return []

    async def save_message(self, role: str, content: str) -> None:
        """Сохранить сообщение в текущей сессии"""
        if self._session_id is None:
            self._session_id = await self._repo.create_session()
        await self._repo.save_message(session_id=self._session_id, role=role, content=content)

    @property
    def session_id(self) -> int | None:
        return self._session_id

    async def list_sessions(self) -> list[SessionInfo]:
        """Список всех сессий для боковой панели."""
        return await self._repo.list_sessions()

    async def switch_session(self, session_id: int) -> list[tuple[str, str]]:
        """Переключиться на другую сессию."""
        self._session_id = session_id
        return await self._repo.load_session_message(session_id)

    async def delete_session(self, session_id: int) -> None:
        """Удалить сессию. Если удаляем текущую - начать новую."""
        await self._repo.delete_session(session_id)
