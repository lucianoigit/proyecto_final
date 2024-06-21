from cx_Freeze import setup, Executable
import os
import sys

# Incrementar la profundidad de recursión
sys.setrecursionlimit(5000)

# Asegúrate de que las rutas estén correctas
base_path = os.path.dirname(__file__)

# Ruta al archivo principal de tu aplicación
main_script = os.path.join(base_path, "main.py")

# Archivos adicionales a incluir
include_files = [
    (os.path.join(base_path, "yolov5s.pt"), "yolov5s.pt"),  # Modelo
    (os.path.join(base_path, "app/esp_interface/icons"), "icons"),  # Iconos
    (os.path.join(base_path, "calibracion"), "calibracion"),  # Archivos de calibración
]

# Dependencias adicionales a incluir
packages = [
    'numpy', 'scipy', 'pandas', 'sklearn', 'torch', 'torchvision', 'opencv-python', 
    'matplotlib', 'seaborn', 'requests', 'pyserial', 'PIL', 'darkdetect', 'customtkinter'
]

# Opciones de construcción
options = {
    'build_exe': {
        'packages': packages,
        'include_files': include_files,
        'zip_include_packages': ['*'],
        'zip_exclude_packages': []
    },
}

# Configuración de cx_Freeze
setup(
    name="DeltaRobot",
    version="0.1",
    description="Aplicación Delta Robot",
    options=options,
    executables=[Executable(main_script, base=None)]
)
