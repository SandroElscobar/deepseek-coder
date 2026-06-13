"""Проверка DeepSeekClient и DeepSeekManager без UI."""

import asyncio

from deepseek_coder.infrastructure.deepseek_client import DeepSeekClient
from deepseek_coder.infrastructure.keyring_store import KeyringStore
from deepseek_coder.services.deepseek import DeepSeekManager


async def main() -> None:
    # Загружаем ключ из keychain
    store = KeyringStore()
    api_key = store.load_api_key()
    if api_key is None:
        print("API-ключ не найден. Сохрани его через KeyringStore.save_api_key()")
        return

    # Собираем зависимости вручную (потом это будет делать app.py)
    client = DeepSeekClient(api_key=api_key, model="deepseek-v4-flash")
    manager = DeepSeekManager(client=client)

    # Тест 1: обычный запрос
    print("=== Тест 1: обычный запрос ===")
    response = await manager.chat("Скажи только: 'Привет от DeepSeek'")
    print(f"Ответ: {response}")
    print(f"Токены: {manager.total_tokens}")

    # Тест 2: streaming
    print("\n=== Тест 2: streaming ===")
    print("Ответ: ", end="", flush=True)
    async for chunk in await manager.chat_stream(
        "Посчитай от 1 до 5, каждое число на новой строке"
    ):
        print(chunk, end="", flush=True)
    print()  # перенос строки после стрима

    # Тест 3: история сохраняется
    print("\n=== Тест 3: контекст диалога ===")
    await manager.chat("Меня зовут Алекс")
    response = await manager.chat("Как меня зовут?")
    print(f"Ответ (должен содержать 'Алекс'): {response}")
    print(f"Сообщений в истории: {len(manager.history)}")


asyncio.run(main())
