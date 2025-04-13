import os
import sys
import platform

APP_NAME = "zenLogBOT"

def get_app_data_path() -> str:
    """Obtiene la ruta a la carpeta de datos de la aplicación específica del usuario."""
    system = platform.system()
    if system == "Windows":
        # %APPDATA% (usualmente C:\Users\<Usuario>\AppData\Roaming)
        base_path = os.getenv('APPDATA')
    elif system == "Darwin": # macOS
        # ~/Library/Application Support/
        base_path = os.path.expanduser('~/Library/Application Support')
    else: # Linux y otros Unix-like
        # ~/.config/ o ~/.local/share/
        base_path = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        if not os.path.isdir(base_path):
             base_path = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
             if not os.path.isdir(base_path):
                 # Fallback si XDG no está definido o no existe
                 base_path = os.path.expanduser('~')

    if not base_path: # Fallback muy genérico si todo falla
        base_path = os.path.expanduser('~')

    app_data_dir = os.path.join(base_path, APP_NAME)
    # Crear directorio si no existe
    os.makedirs(app_data_dir, exist_ok=True)
    return app_data_dir

def get_config_file_path() -> str:
    """Obtiene la ruta completa al archivo config.json en AppData."""
    return os.path.join(get_app_data_path(), "config.json")

def get_bundled_data_path(relative_path: str) -> str:
    """
    Obtiene la ruta absoluta a un archivo de datos, manejando
    ejecución como script y como paquete PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # Si está empaquetado, la base es _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Si es script, la base es el directorio 'nuevobot'
        # Asumiendo que utils.py está en nuevobot/core/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    print(f"App Data Path: {get_app_data_path()}")
    print(f"Config File Path: {get_config_file_path()}")
    print(f"Bundled 'data/lang/en.json' Path: {get_bundled_data_path('data/lang/en.json')}")
    print(f"Bundled 'data/boss_definitions.json' Path: {get_bundled_data_path('data/boss_definitions.json')}")