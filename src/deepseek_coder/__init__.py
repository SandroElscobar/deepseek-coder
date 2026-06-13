import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from qt_material import apply_stylesheet

from deepseek_coder.infrastructure.deepseek_client import DeepSeekClient
from deepseek_coder.infrastructure.keyring_store import KeyringStore
from deepseek_coder.infrastructure.mcp_manager import MCPManager, McpServerConfig
from deepseek_coder.infrastructure.sqlite_repo import ChatRepository
from deepseek_coder.services.deepseek import DeepSeekManager
from deepseek_coder.services.history import ChatHistoryService
from deepseek_coder.services.project import ProjectManager
from deepseek_coder.services.settings import SettingsService
from deepseek_coder.ui.main_window import MainWindow
from deepseek_coder.ui.markdown_renderer import configure
from deepseek_coder.ui.setting_dialog import SettingsDialog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def _main_coroutine(app: QApplication, settings: SettingsService) -> None:
    """Корневая корутина приложения.

    Создаёт главное окно и держится в живых до закрытия приложения,
    чтобы event loop продолжал крутиться и обслуживать Qt-события.
    """
    # Event, который установится при закрытии приложения
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    app.setQuitOnLastWindowClosed(False)
    configure(settings.get_code_style())
    mcp_manager = MCPManager()
    for server_dict in settings.get_mcp_servers():
        try:
            args = server_dict.get("args", [])
            if not isinstance(args, list):
                args = []
            config = McpServerConfig(
                name=str(server_dict["name"]),
                command=str(server_dict["command"]),
                args=list(server_dict.get("args", [])),
            )
            await mcp_manager.start_server(config)
            logger.info("MCP сервер запущен: %s", config.name)
        except Exception as exc:
            logger.error("не удалось запустить MCP сервер %s: %s", server_dict.get("name"), exc)

    repo = ChatRepository()
    project_manager = ProjectManager()
    data_dir = _get_app_data_dir()
    await repo.open(data_dir / "history.db")
    logger.info("База данных открыта")
    api_key = settings.get_api_key()
    if not api_key:
        dialog = SettingsDialog(settings=settings)
        dialog.exec()
        api_key = settings.get_api_key()
        if not api_key:
            app.quit()
            return
    history_service = ChatHistoryService(repo=repo)
    await history_service.restore_last_session()
    client = DeepSeekClient(api_key, model=settings.get_model())
    manager = DeepSeekManager(
        client=client, history_service=history_service, mcp_manager=mcp_manager
    )
    logger.info("История загружена.")
    window = MainWindow(
        manager=manager,
        settings=settings,
        project_manager=project_manager,
        history_service=history_service,
        repo=repo,
        mcp_manager=mcp_manager,
    )
    window.show()
    await window.initialize()
    logger.info("Приложение запущено!")
    await app_close_event.wait()


def _get_app_data_dir() -> Path:
    """
    Возвращает путь к директории для хранения данных,
    Создаёт директорию если ее нет.
    """
    path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    app_data_path = Path(path)
    app_data_path.mkdir(parents=True, exist_ok=True)
    return app_data_path


def _setup_logging(log_path: Path) -> None:
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)


def main() -> int:
    """Точка входа приложения"""
    app = QApplication(sys.argv)
    store = KeyringStore()
    settings = SettingsService(store)
    app.setOrganizationName("DeepSeekCoder")
    app.setApplicationName("DeepSeekCoder")
    data_dir = _get_app_data_dir()
    logger.info(f"Path = {data_dir}")
    _setup_logging(data_dir / "app.log")
    apply_stylesheet(app, theme=settings.get_theme())

    asyncio.run(_main_coroutine(app, settings), loop_factory=QEventLoop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
