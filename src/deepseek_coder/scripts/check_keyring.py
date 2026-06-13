"""Временный скрипт для проверки keyring. Запустить один раз и удалить."""

from deepseek_coder.infrastructure.keyring_store import KeyringStore

store = KeyringStore()

# 1. Сохраняем тестовый ключ
store.save_api_key("test-key-123")
print("Сохранили: test-key-123")

# 2. Читаем обратно
loaded = store.load_api_key()
print(f"Загрузили: {loaded}")
assert loaded == "test-key-123", f"Ожидали 'test-key-123', получили '{loaded}'"

# 3. Удаляем
store.delete_api_key()
print("Удалили")

# 4. Проверяем, что удалилось
after_delete = store.load_api_key()
print(f"После удаления: {after_delete}")
assert after_delete is None, f"Ожидали None, получили '{after_delete}'"

print("\nВсё работает корректно.")
