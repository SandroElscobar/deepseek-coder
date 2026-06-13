> ##### 🇷🇺 [Read to English](README.md) | 🇬🇧 English
# DeepSeek Coder

Desktop AI coding assistant powered by [DeepSeek API](https://platform.deepseek.com/).  
Аналог Claude Code / Cursor — но локальный, без подписки, с открытым кодом.

---

## Возможности

- Streaming-чат с моделями DeepSeek (V4 Flash / V4 Pro)
- История диалогов в локальной SQLite БД
- Открытие проекта — файловое дерево + автоматический контекст для модели
- Встроенные агенты: Code Reviewer, Test Writer, Refactoring Agent, Doc Writer
- MCP серверы — подключение внешних инструментов (файловая система, браузер, и др.)
- Подсветка синтаксиса кода в ответах (Pygments, тема Monokai)
- Отмена запроса в любой момент
- Тёмная тема (qt-material)

---

## Требования

- Python 3.13+
- Windows / macOS / Linux
- [uv](https://github.com/astral-sh/uv) — менеджер пакетов
- API ключ DeepSeek → [platform.deepseek.com](https://platform.deepseek.com/)

---

## Установка и запуск из исходников

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-username/deepseek-coder.git
cd deepseek-coder

# 2. Установить зависимости
uv sync

# 3. Запустить
uv run python -m deepseek_coder
```

При первом запуске откроется диалог настроек — введи API ключ.

---

## Получение API ключа

1. Зарегистрируйся на [platform.deepseek.com](https://platform.deepseek.com/)
2. Перейди в раздел **API Keys** → **Create new key**
3. Скопируй ключ — он показывается только один раз
4. Вставь в настройки приложения (`Ctrl+,` → поле **API-ключ**)

API ключ хранится в системном keychain (Keychain на macOS, Credential Manager на Windows, Secret Service на Linux) — никогда не в файлах на диске.

---

## Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| `Enter` | Отправить сообщение |
| `Shift+Enter` | Новая строка |
| `Ctrl+,` | Открыть настройки |

---

## Открытие проекта

Нажми **📁 Открыть проект** — приложение просканирует директорию и автоматически добавит содержимое файлов в контекст модели. Поддерживаемые расширения: `.py`, `.js`, `.ts`, `.json`, `.md`, `.yaml`, `.toml`, `.html`, `.css`, `.txt`, `.sh`.

При изменении файлов контекст обновляется автоматически.

---

## Агенты

Выбери агента в выпадающем списке слева вверху:

| Агент | Описание |
|-------|----------|
| 💬 Обычный чат | Режим без специального контекста |
| 🔍 Code Reviewer | Анализирует код, находит баги и проблемы |
| 🧪 Test Writer | Пишет pytest-тесты |
| 🔧 Refactoring Agent | Рефакторит по принципам SOLID/DRY/KISS |
| 📝 Doc Writer | Генерирует docstrings в Google стиле |

---

## MCP серверы

MCP (Model Context Protocol) позволяет подключить внешние инструменты — модель сможет читать файлы, искать в интернете, работать с базами данных и т.д.

Настройка: `Ctrl+,` → вкладка **MCP серверы** → **+ Добавить**.

Пример — файловый сервер:
```
Имя:      filesystem
Команда:  npx
Аргументы: -y @modelcontextprotocol/server-filesystem /path/to/your/project
```

Требует Node.js для npx-серверов.

---

## Данные приложения

Все данные хранятся локально:

| Файл | Расположение |
|------|-------------|
| История чатов | `%APPDATA%\DeepSeekCoder\history.db` (Windows) |
| Логи | `%APPDATA%\DeepSeekCoder\app.log` (Windows) |
| Настройки | Реестр Windows / `~/Library/Preferences` (macOS) |
| API ключ | Системный keychain |

На macOS: `~/Library/Application Support/DeepSeekCoder/`  
На Linux: `~/.local/share/DeepSeekCoder/`

---

## Сборка исполняемого файла

```bash
uv run pyinstaller deepseek-coder.spec
```

Готовый `.exe` будет в папке `dist/`.

---

## Разработка

```bash
# Проверка типов
uv run mypy src/

# Линтер
uv run ruff check src/

# Форматирование
uv run ruff format src/
```

---
## Скачать

| Платформа | Ссылка | 
|-----------|--------|
| 🪟 Windows | [DeepSeek-Coder-windows.zip](https://github.com/SandroElscobar/deepseek-coder/releases/latest/download/DeepSeek-Coder-windows.zip) |
| 🍎 macOS | [DeepSeek-Coder-macos.zip](https://github.com/SandroElscobar/deepseek-coder/releases/latest/download/DeepSeek-Coder-macos.zip) |
| 🐧 Linux | [DeepSeek-Coder-linux.zip](https://github.com/SandroElscobar/deepseek-coder/releases/latest/download/DeepSeek-Coder-linux.zip) |


## Лицензия

MIT
