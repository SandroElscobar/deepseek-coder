"""
Сервис для работы с DeepSeek API.

Ответственность:
  - хранение истории диалога в памяти
  - оркестрация запросов через DeepSeekClient
  - подсчёт использованных токенов за сессию
"""

import json
import logging
from collections.abc import AsyncIterator

from deepseek_coder.infrastructure.deepseek_client import (
    DeepSeekClient,
    Message,
    ToolCallMessage,
    ToolResultMessage,
)
from deepseek_coder.infrastructure.mcp_manager import MCPManager
from deepseek_coder.services.history import ChatHistoryService

logger = logging.getLogger(__name__)

TOOL_CALL_PREFIX = "\x00TOOL:"


class DeepSeekManager:
    """Управляет диалогом с DeepSeek: история, токены, отправка.

    Создаётся один раз при запуске приложения и живёт всю сессию.
    """

    def __init__(
        self,
        client: DeepSeekClient,
        history_service: ChatHistoryService | None = None,
        mcp_manager: MCPManager | None = None,
    ) -> None:
        # Клиент приходит снаружи (dependency injection) — не создаём внутри.
        # Это позволяет в тестах подменить его на FakeDeepSeekClient.
        # Системный контекст проекта
        self._system_context: str | None = None
        self._client = client
        # Сервис для работы с историей чата
        self._history_service = history_service
        # История диалога — список сообщений в формате OpenAI.
        # Пополняется при каждом обмене и отправляется целиком при следующем запросе.
        self._history: list[Message | ToolCallMessage | ToolResultMessage] = []
        # MCP менеджер
        self._mcp_manager = mcp_manager

    @property
    def history(self) -> list[Message | ToolCallMessage]:
        """Копия истории диалога — чтобы внешний код не мутировал её напрямую."""
        return list(self._history)

    def clear_history(self) -> None:
        """Очистить историю диалога (кнопка "Новый чат")."""
        self._history.clear()

    def load_history(self, messages: list[tuple[str, str]]) -> None:
        """Загрузить историю из хранилища, заменив текущий контекст."""
        self._history = [Message(role=role, content=content) for role, content in messages]

    async def chat(self, user_message: str) -> str:
        """Отправить сообщение, получить полный ответ, обновить историю."""
        self._history.append(Message(role="user", content=user_message))
        if self._history_service:
            await self._history_service.save_message("user", user_message)

        response_text = await self._client.chat(self._build_messages())

        self._history.append(Message(role="assistant", content=response_text))
        if self._history_service:
            await self._history_service.save_message("assistant", response_text)
        return response_text

    async def chat_stream(self, user_message: str) -> AsyncIterator[str]:
        """Отправить сообщение, получать ответ чанками, обновить историю."""
        self._history.append(Message(role="user", content=user_message))

        # Собираем полный текст ответа по ходу стриминга,
        # чтобы добавить его в историю одним сообщением после завершения.
        full_response: list[str] = []
        try:
            if self._history_service:
                await self._history_service.save_message("user", user_message)
            async for chunk in self._client.chat_stream(self._build_messages()):
                full_response.append(chunk)
                yield chunk
        finally:
            self._history.append(Message(role="assistant", content="".join(full_response)))
            if self._history_service:
                await self._history_service.save_message("assistant", "".join(full_response))

    def set_system_context(self, context: str | None) -> None:
        self._system_context = context

    def _build_messages(self) -> list[Message | ToolCallMessage | ToolResultMessage]:
        if self._system_context:
            result = [
                Message(role="system", content=self._system_context),
                *self._history,
            ]
            return result
        return list(self._history)

    @property
    def system_context(self) -> str | None:
        return self._system_context

    async def new_chat(self) -> None:
        """Начать новый диалог - очистить историю и создать новую сессию"""
        self._history = []
        if self._history_service:
            await self._history_service.start_new_session()

    def _build_tools(self) -> list[dict[str, object]] | None:
        """Собрать список tools для PI из всех MCP серверов."""
        if self._mcp_manager is None:
            return None
        tools = self._mcp_manager.list_tools()
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools
        ]

    async def run_agent_loop(self, user_message: str) -> AsyncIterator[str]:
        """Агентский цикл LLM -> tool call -> результат -> LLM -> ..."""
        self._history.append(Message(role="user", content=user_message))
        if self._history_service:
            await self._history_service.save_message("user", user_message)

        while True:
            # Запрашиваем у модели следующий шаг
            tools = self._build_tools()
            response = await self._client.chat_with_tools(self._build_messages(), tools)

            if response.finish_reason == "tool_calls":
                # Модель хочет вызвать tool
                for tool_call in response.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    yield f"{TOOL_CALL_PREFIX}{tool_call.function.name}"
                    if self._mcp_manager is None:
                        return
                    result = await self._mcp_manager.call_tool(tool_call.function.name, args)
                    # Добавляем результат в историю
                    self._history.append(
                        ToolCallMessage(
                            role="assistant",
                            content=None,
                            tool_calls=[tool_call.model_dump()],
                            reasoning_content=response.reasoning_content,
                        )
                    )
                    self._history.append(
                        ToolResultMessage(role="tool", tool_call_id=tool_call.id, content=result)
                    )

            else:
                # Финальный ответ
                text = response.content or ""
                self._history.append(Message(role="assistant", content=text))
                if self._history_service:
                    await self._history_service.save_message("assistant", text)
                yield text
                break

    async def chat_auto(self, user_message: str) -> AsyncIterator[str]:
        tools = self._build_tools()
        if tools:
            async for chunk in self.run_agent_loop(user_message):
                yield chunk
        else:
            async for chunk in self.chat_stream(user_message):
                yield chunk
