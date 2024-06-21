# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final'],
    binaries=[],
    datas=[
        ('C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final\\yolov5s.pt', 'yolov5s.pt'),
        ('C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final\\app\\esp_interface\\icons\\connectivity.png', 'app/esp_interface/icons/connectivity.png'),
        ('C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final\\app\\esp_interface\\icons\\start.png', 'app/esp_interface/icons/start.png'),
        ('C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final\\app\\esp_interface\\icons\\settings.png', 'app/esp_interface/icons/settings.png'),
        ('C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final\\app\\esp_interface\\icons\\dashboard.png', 'app/esp_interface/icons/dashboard.png'),
        ('C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final\\app\\esp_interface\\icons\\close.png', 'app/esp_interface/icons/close.png'),
        ('C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final\\app\\esp_interface\\icons\\iniciar.png', 'app/esp_interface/icons/iniciar.png'),
        ('C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final\\app\\esp_interface\\icons\\stop.png', 'app/esp_interface/icons/stop.png'),
        ('C:\\Users\\lucas\\OneDrive\\Escritorio\\luciano\\proyecto_final\\calibracion', 'calibracion'),
    ],
    hiddenimports=[],
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
    name='main',
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
)

