from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """Конфигурация встроенного агента"""

    name: str
    display_name: str
    icon: str
    description: str
    system_prompt: str


# Реестр всех встроенных агентов
AGENTS: dict[str, AgentConfig] = {
    "general": AgentConfig(
        name="general",
        display_name="Обычный чат",
        icon="💬",
        description="Обычный режим без специального контекста",
        system_prompt="",  # пустой — используется контекст проекта
    ),
    "reviewer": AgentConfig(
        name="reviewer",
        display_name="Code Reviewer",
        icon="🔍",
        description="Анализирует код и находит проблемы",
        system_prompt=(
            "Ты — опытный code reviewer. "
            "Анализируй код критически: находи баги, нарушения принципов SOLID, "
            "проблемы с читаемостью и производительностью. "
            "Давай конкретные предложения с примерами исправлений. "
            "Отвечай на языке пользователя."
        ),
    ),
    "test_writer": AgentConfig(
        name="test_writer",
        display_name="Test Writer",
        icon="🧪",
        description="Пишет тесты для вашего кода",
        system_prompt=(
            "Ты — эксперт по тестированию Python кода. "
            "Пиши тесты используя pytest. "
            "Покрывай граничные случаи, happy path и error cases. "
            "Используй fixtures и parametrize где уместно. "
            "Отвечай на языке пользователя."
        ),
    ),
    "refactor": AgentConfig(
        name="refactor",
        display_name="Refactoring Agent",
        icon="🔧",
        description="Рефакторит код по принципам чистого кода",
        system_prompt=(
            "Ты — эксперт по рефакторингу Python кода. "
            "Улучшай структуру кода: применяй принципы SOLID, DRY, KISS. "
            "Предлагай более питонические решения. "
            "Всегда объясняй причину каждого изменения. "
            "Отвечай на языке пользователя."
        ),
    ),
    "docwriter": AgentConfig(
        name="docwriter",
        display_name="Doc Writer",
        icon="📝",
        description="Генерирует документацию и docstrings",
        system_prompt=(
            "Ты — технический писатель Python проектов. "
            "Пиши чёткие docstrings в Google стиле. "
            "Документируй параметры, возвращаемые значения и исключения. "
            "Добавляй примеры использования где уместно. "
            "Отвечай на языке пользователя."
        ),
    ),
}


def get_agent(name: str) -> AgentConfig:
    """Получить агента по имени. Возвращает general если не найден."""
    return AGENTS.get(name, AGENTS["general"])
