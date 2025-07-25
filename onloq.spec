# -*- mode: python ; coding: utf-8 -*-
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))
src_dir = os.path.join(current_dir, 'src')

a = Analysis(
    ['main.py'],
    pathex=[current_dir, src_dir],
    binaries=[],
    datas=[
        (os.path.join(current_dir, 'icon.png'), '.'),
    ],
    hiddenimports=[
        'cli',
        'cli.main',
        'logger',
        'logger.activity_logger',
        'logger.code_logger',
        'storage',
        'storage.database',
        'summarizer',
        'summarizer.llm_summarizer',
        'scheduler',
        'scheduler.daily_scheduler',
        'scheduler.notifier',
        'utils',
        'utils.config',
        'typer',
        'rich',
        'psutil',
        'watchdog',
        'pynput',
        'win32gui',
        'win32process',
        'win32con',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='onloq',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.png'],
)
