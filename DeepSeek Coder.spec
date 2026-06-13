# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

# Путь к qt_material — нужен для включения тем и шрифтов
import qt_material
QT_MATERIAL_DIR = Path(qt_material.__file__).parent

a = Analysis(
    [str(Path('src') / 'deepseek_coder' / '__main__.py')],
    pathex=[],
    binaries=[],
    datas=[
        # Темы, шрифты и ресурсы qt_material
        # Формат: (откуда, куда внутри bundle)
        (str(QT_MATERIAL_DIR / 'themes'), 'qt_material/themes'),
        (str(QT_MATERIAL_DIR / 'fonts'), 'qt_material/fonts'),
        (str(QT_MATERIAL_DIR / 'resources'), 'qt_material/resources'),
        (str(QT_MATERIAL_DIR / 'material.qss.template'), 'qt_material'),
    ],
    hiddenimports=[
        # qt_material загружает темы динамически — PyInstaller не видит их статически
        'qt_material',
        # keyring использует backend через importlib — нужно указать явно для Windows
        'keyring.backends.Windows',
        # aiosqlite использует sqlite3 внутри — обычно находится, но на всякий случай
        'aiosqlite',
        # markdown-it-py плагины
        'markdown_it',
        'markdown_it.presets',
        # Pygments лексеры и форматтеры загружаются динамически
        'pygments.lexers',
        'pygments.formatters',
        'pygments.styles',
    ],
    # hookspath — папка с нашими хуками (пока пустая)
    # qt_material поставляет свой хук, но он лежит внутри пакета
    hookspath=[str(QT_MATERIAL_DIR)],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Исключаем то что точно не нужно — уменьшает размер билда
        'tkinter',
        'unittest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DeepSeek Coder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # GUI приложение — без консольного окна
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        # PyQt6 DLL нельзя сжимать через UPX — они ломаются
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'Qt6Network.dll',
    ],
    name='DeepSeek Coder',
)
