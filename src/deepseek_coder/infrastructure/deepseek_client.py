from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, TypedDict

from openai import AsyncOpenAI


class Message(TypedDict):
    role: str
    content: str


class ToolCallMessage(TypedDict):
    """Сообщение ассистента с вызовом tool"""

    role: str
    content: str | None
    tool_calls: list[dict[str, Any]]
    reasoning_content: str | None


class ToolResultMessage(TypedDict):
    """Результат выполнения tool."""

    role: str
    tool_call_id: str
    content: str


@dataclass
class ToolCallResult:
    """Результат запроса"""

    finish_reason: str
    content: str | None
    tool_calls: list[Any]
    reasoning_content: str | None = None


class DeepSeekClient:
    """Адаптер для DeepSeek API поверх OpenAI SDK."""

    BASE_URL = "https://api.deepseek.com"

    def __init__(self, api_key: str, model: str):
        # AsyncOpenAI — клиент для асинхронных запросов.
        # Base_url перенаправляет все запросы на DeepSeek вместо OpenAI.
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
        )
        self._model = model

    async def chat(self, messages: list[Message | ToolCallMessage | ToolResultMessage]) -> str:
        """Отправить сообщения, получить полный ответ.

        Используется когда streaming не нужен — например, для тестирования
        или для коротких запросов, где задержка не критична.
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
        )
        return response.choices[0].message.content or ""

    async def chat_stream(
        self, messages: list[Message | ToolCallMessage | ToolResultMessage]
    ) -> AsyncIterator[str]:
        """Отправить сообщения, получать ответ чанками по мере генерации.
        Yields:
            Фрагменты текста ответа по мере их поступления от API.
        """
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta is not None:
                yield delta

    async def chat_with_tools(
        self,
        messages: list[Message | ToolCallMessage | ToolResultMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> ToolCallResult:
        """Отправить сообщение с tools, вернуть результат"""
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        reasoning = getattr(choice.message, "reasoning_content", None)
        return ToolCallResult(
            finish_reason=choice.finish_reason or "stop",
            content=choice.message.content,
            tool_calls=choice.message.tool_calls or [],
            reasoning_content=reasoning,
        )
