# Punto de entrada principal para la aplicación de escritorio

import os
import json
import sys

# La función ensure_data_files_exist se elimina, StateManager maneja config.json
# y LocalizationManager/LogUploader manejan la carga de datos empaquetados.

# Función para manejar el cierre de la ventana
def on_closing(app_instance, manager_instance):
    """Llamado cuando se intenta cerrar la ventana."""
    print("Cerrando la aplicación...")
    if manager_instance:
        manager_instance.shutdown() # Llama al shutdown del StateManager
    app_instance.destroy() # Cierra la ventana de Tkinter
    print("Ventana cerrada.")
    # sys.exit() # Opcional: forzar salida si hay hilos no daemon


if __name__ == "__main__":
    # Cambiar al directorio del script para que las rutas relativas funcionen
    # para PyInstaller (_MEIPASS) y ejecución normal.
    if getattr(sys, 'frozen', False):
        # Si está empaquetado
        application_path = sys._MEIPASS
        # Cambiar CWD a la carpeta temporal puede ser problemático si
        # se esperan archivos relativos al .exe original.
        # Es mejor que las funciones de utils determinen las rutas correctas.
        # os.chdir(application_path) # Comentado - Usar utils.get_bundled_data_path
        print(f"Running from PyInstaller bundle: {application_path}")
    else:
        # Si se ejecuta como script
        application_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(application_path) # Cambiar CWD al directorio del script
        print(f"Running as script from: {application_path}")

    # Importar clases después de asegurar directorio (si aplica)
    from core.state_manager import StateManager
    from ui.app import App

    print("Iniciando StateManager...")
    # StateManager ahora carga/crea config.json en AppData
    state_manager = StateManager()

    print("Iniciando Aplicación UI...")
    app = App(state_manager=state_manager)

    # Conectar la instancia de la UI al StateManager
    print("Conectando UI y StateManager...")
    state_manager.set_ui_app(app)
    # Pasar el método de logging de la UI al StateManager
    state_manager.set_ui_logger(app.log_message)

    # Configurar el manejador de cierre de ventana
    app.protocol("WM_DELETE_WINDOW", lambda: on_closing(app, state_manager))

    print("Ejecutando mainloop...")
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nInterrupción por teclado detectada.")
        on_closing(app, state_manager) # Intentar cierre limpio

    print("Aplicación finalizada.")