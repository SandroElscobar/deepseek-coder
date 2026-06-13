from __future__ import annotations

import asyncio
import contextlib
import logging
from asyncio import Task
from dataclasses import dataclass, field

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

logger = logging.getLogger(__name__)


@dataclass
class McpServerConfig:
    """Конфигурация одного MCP сервера"""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None


@dataclass
class _ServerState:
    """Внутреннее состояние MCP сервера"""

    config: McpServerConfig
    session: ClientSession
    tools: list[Tool] = field(default_factory=list)
    task: Task[None] | None = None


class MCPManager:
    """Управляет жизненным циклом MCP сервера.
    Запускает серверы как subprocesses, держит сессии открытыми,
    предоставляет unified список tools для DeepSeekManager.
    """

    def __init__(self) -> None:
        # Имя сервера и его состояния
        self._servers: dict[str, _ServerState] = {}

    async def start_server(self, config: McpServerConfig) -> None:
        """Запустить MCP сервер инициализировать сессию"""
        params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env,
        )
        ready = asyncio.Event()
        session_holder: list[tuple[ClientSession, list[Tool]]] = []

        async def _run() -> None:
            async with stdio_client(params) as (read, write):  # noqa: SIM117
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    session_holder.append((session, tools_result.tools))
                    ready.set()
                    await asyncio.Event().wait()

        task = asyncio.create_task(_run())
        await ready.wait()

        session, tools = session_holder[0]
        self._servers[config.name] = _ServerState(
            config=config, session=session, tools=tools, task=task
        )

    async def stop_server(self, name: str) -> None:
        """Остановить сервер"""
        state = self._servers.pop(name, None)
        if state is None:
            return
        if state.task is not None:
            state.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await state.task

    def list_tools(self) -> list[Tool]:
        """Получить все tools от всех запущенных сервер"""
        tools: list[Tool] = []
        for state in self._servers.values():
            tools.extend(state.tools)
        return tools

    async def call_tool(self, tool_name: str, arguments: dict[str, object]) -> str:
        """Вызвать tool по имени, найти нужный сервер автоматически."""
        state = self._find_server_for_tool(tool_name)
        if state is None:
            return f"[Ошибка: tool '{tool_name}' не найден]"
        result = await state.session.call_tool(tool_name, arguments)
        return "\n".join(block.text for block in result.content if hasattr(block, "text"))

    def _find_server_for_tool(self, tool_name: str) -> _ServerState | None:
        """Найти сервер который предоставляет данный tool."""
        for state in self._servers.values():
            for tool in state.tools:
                if tool.name == tool_name:
                    return state
        return None

    @property
    def servers(self):
        return self._servers

    async def stop_all(self) -> None:
        """Остановить все запущенные серверы."""
        for name in list(self._servers.keys()):
            await self.stop_server(name)
