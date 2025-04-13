import customtkinter as ctk
import datetime # Para timestamp en log
import os # Para construir la ruta del icono
import sys # Para determinar si es ejecutable empaquetado (PyInstaller)

# Importar vistas con importación absoluta
from ui.views.config_view import ConfigView # Cambiado
from ui.views.selection_view import SelectionView # Cambiado
# from .views.history_view import HistoryView # Eliminado

# Importar state manager y utils con importación absoluta
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from core.state_manager import StateManager # Cambiado
    from core.localization import LocalizationManager # Cambiado
from core.utils import get_bundled_data_path # Cambiado

class App(ctk.CTk):
    """Clase principal de la aplicación UI."""

    LOG_MAX_LINES = 200

    def __init__(self, state_manager: 'Optional[StateManager]' = None):
        super().__init__()

        self.state_manager = state_manager
        self.loc_manager: 'Optional[LocalizationManager]' = self.state_manager.loc_manager if self.state_manager else None

        # Obtener textos iniciales
        initial_title = self.get_string("app_title")
        nav_header = self.get_string("nav_header")
        nav_upload = self.get_string("nav_upload")
        nav_config = self.get_string("nav_config")
        log_area_label = self.get_string("log_area_label")
        footer_text = "zenLogBOT v1.0 by LeShock | LeShock.5261"


        self.title(initial_title)
        window_width = 800
        window_height = 780
        self.geometry(f"{window_width}x{window_height}")

        # Centrar Ventana
        self.center_window(window_width, window_height)

        # Establecer Icono
        try:
            icon_path = get_bundled_data_path("favicon.ico")
            if os.path.exists(icon_path): self.iconbitmap(icon_path); print(f"Icono establecido desde: {icon_path}")
            else: print(f"Advertencia: Archivo de icono no encontrado en {icon_path}")
        except Exception as e: print(f"Error al establecer el icono: {e}")

        # Configurar apariencia
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Layout Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0) # Footer

        # Frame de Navegación
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(3, weight=1)
        self.navigation_frame_label = ctk.CTkLabel(self.navigation_frame, text=nav_header, font=ctk.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)
        self.select_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text=nav_upload, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", command=self.select_button_event)
        self.select_button.grid(row=1, column=0, sticky="ew")
        self.config_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text=nav_config, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", command=self.config_button_event)
        self.config_button.grid(row=2, column=0, sticky="ew")

        # Frame Principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=(20, 10))
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Log Box
        self.log_frame = ctk.CTkFrame(self, corner_radius=0)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 5))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_label = ctk.CTkLabel(self.log_frame, text=log_area_label, font=ctk.CTkFont(size=13))
        self.log_label.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="w")
        self.log_textbox = ctk.CTkTextbox(self.log_frame, height=120, state="disabled", wrap="word")
        self.log_textbox.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="nsew")

        # Footer
        self.footer_label = ctk.CTkLabel(self, text=footer_text, font=ctk.CTkFont(size=10), text_color="gray")
        self.footer_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))

        # Inicializar Vistas
        self.selection_frame = SelectionView(self.main_frame, state_manager=self.state_manager)
        self.config_frame = ConfigView(self.main_frame, state_manager=self.state_manager)

        # Seleccionar vista inicial
        self.select_frame_by_name("upload")

    def center_window(self, width, height):
        """Centra la ventana en la pantalla."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        print(f"Ventana centrada en: {int(x)}, {int(y)}")

    def get_string(self, key: str, **kwargs) -> str:
        """Obtiene la cadena localizada o la clave si falla."""
        if self.loc_manager: return self.loc_manager.get_string(key, **kwargs)
        return key

    def select_frame_by_name(self, name):
        """Muestra el frame correspondiente al botón presionado."""
        self.select_button.configure(fg_color=("gray75", "gray25") if name == "upload" else "transparent")
        self.config_button.configure(fg_color=("gray75", "gray25") if name == "config" else "transparent")
        self.selection_frame.grid_forget()
        self.config_frame.grid_forget()
        if name == "upload": self.selection_frame.grid(row=0, column=0, sticky="nsew")
        elif name == "config": self.config_frame.grid(row=0, column=0, sticky="nsew")

    # Eventos de Botones de Navegación
    def select_button_event(self): self.select_frame_by_name("upload")
    def config_button_event(self): self.select_frame_by_name("config")

    # Método para añadir mensajes al Log Box
    def log_message(self, message: str):
        """Añade un mensaje al área de texto de log."""
        try:
            if not self.log_textbox or not self.log_textbox.winfo_exists(): print("LogBox no disponible:", message); return
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", log_entry)
            lines = int(self.log_textbox.index("end-1c").split('.')[0])
            if lines > self.LOG_MAX_LINES:
                lines_to_delete = lines - self.LOG_MAX_LINES
                self.log_textbox.delete("1.0", f"{lines_to_delete + 1}.0")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        except Exception as e: print(f"Error al loguear en UI: {e}"); print("Mensaje original:", message)

    # Método para ser llamado por StateManager para actualizar textos
    def update_language_display(self, loc_manager: 'LocalizationManager'):
         """Actualiza los textos de esta ventana principal y sus vistas hijas."""
         self.loc_manager = loc_manager
         self.title(self.get_string("app_title"))
         self.navigation_frame_label.configure(text=self.get_string("nav_header"))
         self.select_button.configure(text=self.get_string("nav_upload"))
         self.config_button.configure(text=self.get_string("nav_config"))
         self.log_label.configure(text=self.get_string("log_area_label"))
         self.footer_label.configure(text=self.get_string("footer_text"))
         if hasattr(self, 'config_frame') and hasattr(self.config_frame, 'update_language_display'): self.config_frame.update_language_display(loc_manager)
         if hasattr(self, 'selection_frame') and hasattr(self.selection_frame, 'update_language_display'): self.selection_frame.update_language_display(loc_manager)

if __name__ == "__main__":
    # --- Código de prueba adaptado ---
    import os; import json
    try: from core.utils import get_bundled_data_path
    except ImportError: get_bundled_data_path = lambda p: p # Fallback simple
    try: from core.localization import LocalizationManager as MockLocalizationManager # Usar real si es posible
    except ImportError:
        class MockLocalizationManager:
            def __init__(self, lang="en"): self.strings = {}; self.load_language(lang)
            def get_string(self, key, **kwargs): return self.strings.get(key, key).format(**kwargs)
            def load_language(self, lang_code):
                try:
                    lang_path = get_bundled_data_path(f"data/lang/{lang_code}.json")
                    with open(lang_path, 'r', encoding='utf-8') as f: self.strings = json.load(f)
                except: self.strings = {"app_title": "Error Loading Lang", "footer_text": "Mock Footer"}
    class MockStateManager:
         def __init__(self): self.loc_manager = MockLocalizationManager(); self.ui_logger = print; self.config = {"language": "en"}
         def get_localized_string(self, key, **kwargs): return self.loc_manager.get_string(key, **kwargs)
         def config_updated(self): print("MockStateManager: Config Updated"); self.update_ui_language()
         def start_upload(self, sel, dur, title): print(f"MockStateManager: Start Upload {sel}, Dur: {dur}, Title: '{title}'"); self.ui_logger("Upload Started...")
         def update_ui_language(self): print("MockStateManager: Updating UI Language"); app.update_language_display(self.loc_manager)
         def set_ui_logger(self, logger_func): self.ui_logger = logger_func
         class MockLogUploader: boss_definitions = {}
         log_uploader = MockLogUploader()

    data_dir_path = get_bundled_data_path("data"); lang_dir_path = get_bundled_data_path("data/lang")
    if not os.path.exists(data_dir_path): os.makedirs(data_dir_path)
    if not os.path.exists(lang_dir_path): os.makedirs(lang_dir_path)
    for lang_code in ["en", "es"]:
        lang_path = os.path.join(lang_dir_path, f"{lang_code}.json")
        if not os.path.exists(lang_path):
             try:
                 with open(lang_path, "w", encoding='utf-8') as f: json.dump({"app_title": f"Title ({lang_code})", "footer_text": f"Footer ({lang_code})"}, f)
             except IOError: pass
    icon_p = get_bundled_data_path("favicon.ico")
    if not os.path.exists(icon_p): print(f"Advertencia: {icon_p} no encontrado...")
    defs_path = get_bundled_data_path("data/boss_definitions.json")
    if not os.path.exists(defs_path):
         dummy_defs = { "raids": { "W1": { "Test Boss": { "name": ["Test Boss Folder"] } } } }
         with open(defs_path, "w") as f: json.dump(dummy_defs, f)
    try:
        with open(defs_path, 'r') as f: MockStateManager.MockLogUploader.boss_definitions = json.load(f)
    except: pass

    mock_manager = MockStateManager()
    app = App(state_manager=mock_manager)
    mock_manager.set_ui_logger(app.log_message)
    app.update_language_display(mock_manager.loc_manager)
    app.mainloop()