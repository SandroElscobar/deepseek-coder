> ##### 🇷🇺 [Читать на русском](README.ru.md) | 🇬🇧 Russian
# DeepSeek Coder

Desktop AI coding assistant powered by [DeepSeek API](https://platform.deepseek.com/).  
An open-source alternative to Claude Code / Cursor — local, no subscription required.

---

## Features

- Streaming chat with DeepSeek models (V4 Flash / V4 Pro)
- Persistent chat history in a local SQLite database
- Project explorer — file tree with automatic context injection into the model
- Built-in agents: Code Reviewer, Test Writer, Refactoring Agent, Doc Writer
- MCP servers — connect external tools (filesystem, browser, databases, etc.)
- Syntax highlighting in model responses (Pygments, Monokai theme)
- Cancel any in-progress request at any time
- Dark theme (qt-material)

---

## Requirements

- Python 3.13+
- Windows / macOS / Linux
- [uv](https://github.com/astral-sh/uv) — package manager
- DeepSeek API key → [platform.deepseek.com](https://platform.deepseek.com/)

---

## Installation & Running from Source

```bash
# 1. Clone the repository
git clone https://github.com/your-username/deepseek-coder.git
cd deepseek-coder

# 2. Install dependencies
uv sync

# 3. Run
uv run python -m deepseek_coder
```

On first launch, a settings dialog will open — enter your API key there.

---

## Getting an API Key

1. Sign up at [platform.deepseek.com](https://platform.deepseek.com/)
2. Go to **API Keys** → **Create new key**
3. Copy the key — it is shown only once
4. Paste it in the app settings (`Ctrl+,` → **API Key** field)

The API key is stored in the system keychain (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux) — never in plain text files on disk.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift+Enter` | New line |
| `Ctrl+,` | Open settings |

---

## Opening a Project

Click **📁 Open Project** — the app will scan the directory and automatically inject file contents into the model's context. Supported extensions: `.py`, `.js`, `.ts`, `.json`, `.md`, `.yaml`, `.toml`, `.html`, `.css`, `.txt`, `.sh`.

Context updates automatically when files change.

---

## Agents

Select an agent from the dropdown in the top-left:

| Agent | Description |
|-------|-------------|
| 💬 General Chat | No special context |
| 🔍 Code Reviewer | Analyzes code, finds bugs and issues |
| 🧪 Test Writer | Writes pytest tests |
| 🔧 Refactoring Agent | Refactors following SOLID/DRY/KISS principles |
| 📝 Doc Writer | Generates Google-style docstrings |

---

## MCP Servers

MCP (Model Context Protocol) lets you connect external tools — the model can read files, search the web, query databases, and more.

Setup: `Ctrl+,` → **MCP Servers** tab → **+ Add**.

Example — filesystem server:
```
Name:      filesystem
Command:   npx
Arguments: -y @modelcontextprotocol/server-filesystem /path/to/your/project
```

npx-based servers require Node.js.

---

## Application Data

All data is stored locally:

| File | Location |
|------|----------|
| Chat history | `%APPDATA%\DeepSeekCoder\history.db` (Windows) |
| Logs | `%APPDATA%\DeepSeekCoder\app.log` (Windows) |
| Settings | Windows Registry / `~/Library/Preferences` (macOS) |
| API key | System keychain |

On macOS: `~/Library/Application Support/DeepSeekCoder/`  
On Linux: `~/.local/share/DeepSeekCoder/`

---

## Building an Executable

```bash
uv run pyinstaller deepseek-coder.spec
```

The resulting `.exe` will be in the `dist/` folder.

---

## Development

```bash
# Type checking
uv run mypy src/

# Linter
uv run ruff check src/

# Formatting
uv run ruff format src/
```

---

## Скачать

| Платформа | Ссылка | 
|-----------|--------|
| 🪟 Windows | [DeepSeek-Coder-windows.zip](https://github.com/SandroElscobar/deepseek-coder/releases/latest/download/DeepSeek-Coder-windows.zip) |
| 🍎 macOS | [DeepSeek-Coder-macos.zip](https://github.com/SandroElscobar/deepseek-coder/releases/latest/download/DeepSeek-Coder-macos.zip) |
| 🐧 Linux | [DeepSeek-Coder-linux.zip](https://github.com/SandroElscobar/deepseek-coder/releases/latest/download/DeepSeek-Coder-linux.zip) |

## License

MIT
