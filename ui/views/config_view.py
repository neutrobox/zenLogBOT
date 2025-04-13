import customtkinter as ctk
from tkinter import filedialog
import json
import os
from typing import TYPE_CHECKING, Optional

# Importar state manager con importación absoluta
if TYPE_CHECKING:
    from core.state_manager import StateManager # Cambiado

class ConfigView(ctk.CTkFrame):
    """Vista para configurar el token del bot, ID de canal, idioma y la ruta de logs."""

    def __init__(self, master, state_manager: 'Optional[StateManager]' = None):
        super().__init__(master)
        self.state_manager = state_manager
        self.lm = self.state_manager.loc_manager if self.state_manager else None
        self.current_config = self.state_manager.config if self.state_manager else {}

        self.grid_columnconfigure(1, weight=1)

        # --- Token de Discord ---
        self.token_label = ctk.CTkLabel(self, text=self.get_string("config_token_label"))
        self.token_label.grid(row=0, column=0, padx=(20, 5), pady=(10, 5), sticky="w")
        self.token_entry = ctk.CTkEntry(self, placeholder_text=self.get_string("config_token_placeholder"), width=300)
        self.token_entry.grid(row=0, column=1, columnspan=2, padx=(5, 20), pady=(10, 5), sticky="ew")
        self.token_entry.insert(0, self.current_config.get("discord_token", ""))

        # --- ID Canal Discord ---
        self.channel_id_label = ctk.CTkLabel(self, text=self.get_string("config_channel_id_label"))
        self.channel_id_label.grid(row=1, column=0, padx=(20, 5), pady=5, sticky="w")
        self.channel_id_entry = ctk.CTkEntry(self, placeholder_text=self.get_string("config_channel_id_placeholder"), width=300)
        self.channel_id_entry.grid(row=1, column=1, columnspan=2, padx=(5, 20), pady=5, sticky="ew")
        self.channel_id_entry.insert(0, self.current_config.get("target_channel_id", ""))

        # --- Ruta Carpeta Logs ---
        self.path_label = ctk.CTkLabel(self, text=self.get_string("config_log_path_label"))
        self.path_label.grid(row=2, column=0, padx=(20, 5), pady=5, sticky="w")
        self.path_entry = ctk.CTkEntry(self, placeholder_text=self.get_string("config_log_path_placeholder"), width=300)
        self.path_entry.grid(row=2, column=1, padx=(5, 5), pady=5, sticky="ew")
        self.path_entry.insert(0, self.current_config.get("log_folder_path", ""))
        self.browse_button = ctk.CTkButton(self, text=self.get_string("config_browse_button"), width=100, command=self.browse_folder)
        self.browse_button.grid(row=2, column=2, padx=(5, 20), pady=5, sticky="w")

        # --- Token de Usuario dps.report (Opcional) ---
        self.dps_token_label = ctk.CTkLabel(self, text=self.get_string("config_dps_token_label"))
        self.dps_token_label.grid(row=3, column=0, padx=(20, 5), pady=5, sticky="w")
        self.dps_token_entry = ctk.CTkEntry(self, placeholder_text=self.get_string("config_dps_token_placeholder"), width=300)
        self.dps_token_entry.grid(row=3, column=1, columnspan=2, padx=(5, 20), pady=5, sticky="ew")
        self.dps_token_entry.insert(0, self.current_config.get("dps_report_user_token", ""))

        # --- Selección de Idioma ---
        self.lang_label = ctk.CTkLabel(self, text=self.get_string("config_language_label"))
        self.lang_label.grid(row=4, column=0, padx=(20, 5), pady=5, sticky="w")
        self.lang_options = ["English", "Español"]
        self.lang_map = {"English": "en", "Español": "es"}
        self.reverse_lang_map = {v: k for k, v in self.lang_map.items()}
        self.lang_combobox = ctk.CTkComboBox(self, values=self.lang_options, command=self.language_changed)
        self.lang_combobox.grid(row=4, column=1, columnspan=2, padx=(5, 20), pady=5, sticky="ew")
        current_lang_code = self.current_config.get("language", "en")
        current_lang_display = self.reverse_lang_map.get(current_lang_code, "English")
        self.lang_combobox.set(current_lang_display)

        # --- Botón Guardar ---
        self.save_button = ctk.CTkButton(self, text=self.get_string("config_save_button"), command=self.save_button_action)
        self.save_button.grid(row=5, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="ew")

        # --- Mensaje de Estado ---
        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.grid(row=6, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="ew")

    def get_string(self, key: str, **kwargs) -> str:
        """Obtiene la cadena localizada o la clave si falla."""
        if self.lm: return self.lm.get_string(key, **kwargs)
        return key

    def browse_folder(self):
        """Abre un diálogo para seleccionar la carpeta de logs."""
        initial_dir = self.path_entry.get()
        if not os.path.isdir(initial_dir): initial_dir = "/"
        folder_path = filedialog.askdirectory(
            title=self.get_string("config_browse_dialog_title"),
            initialdir=initial_dir
        )
        if folder_path:
            self.path_entry.delete(0, ctk.END)
            self.path_entry.insert(0, folder_path)
            self.status_label.configure(text="")

    def language_changed(self, choice):
        """Llamado cuando se selecciona un idioma en el ComboBox."""
        pass # La lógica se maneja al guardar

    def save_button_action(self):
        """Recoge los datos de la UI y llama al StateManager para guardarlos."""
        if not self.state_manager:
            self.status_label.configure(text="Error: StateManager no disponible.", text_color="red")
            return

        data_to_save = {
            "discord_token": self.token_entry.get().strip(),
            "target_channel_id": self.channel_id_entry.get().strip(),
            "log_folder_path": self.path_entry.get().strip(),
            "dps_report_user_token": self.dps_token_entry.get().strip(),
            "language": self.lang_map.get(self.lang_combobox.get(), "en")
        }

        if not data_to_save["discord_token"]:
             self.status_label.configure(text=self.get_string("config_status_error_token"), text_color="red")
             return
        if not data_to_save["target_channel_id"]:
             self.status_label.configure(text=self.get_string("config_status_error_channel_id"), text_color="red")
             return
        if not data_to_save["log_folder_path"] or not os.path.isdir(data_to_save["log_folder_path"]):
             self.status_label.configure(text=self.get_string("config_status_error_log_path"), text_color="red")
             return
        try:
            int(data_to_save["target_channel_id"])
        except ValueError:
            self.status_label.configure(text=self.get_string("config_status_error_channel_id_numeric"), text_color="red")
            return

        save_successful = self.state_manager.save_configuration(data_to_save)

        if save_successful:
            self.status_label.configure(text=self.get_string("config_status_saved"), text_color="green")
        # else: # StateManager ya loguea el error

    def update_language_display(self, loc_manager):
        """Actualiza los textos de esta vista."""
        self.lm = loc_manager
        self.token_label.configure(text=self.get_string("config_token_label"))
        self.token_entry.configure(placeholder_text=self.get_string("config_token_placeholder"))
        self.channel_id_label.configure(text=self.get_string("config_channel_id_label"))
        self.channel_id_entry.configure(placeholder_text=self.get_string("config_channel_id_placeholder"))
        self.path_label.configure(text=self.get_string("config_log_path_label"))
        self.path_entry.configure(placeholder_text=self.get_string("config_log_path_placeholder"))
        self.browse_button.configure(text=self.get_string("config_browse_button"))
        self.dps_token_label.configure(text=self.get_string("config_dps_token_label"))
        self.dps_token_entry.configure(placeholder_text=self.get_string("config_dps_token_placeholder"))
        self.lang_label.configure(text=self.get_string("config_language_label"))
        self.save_button.configure(text=self.get_string("config_save_button"))

# --- Para pruebas directas de esta vista ---
if __name__ == "__main__":
    # Simular LocalizationManager básico
    class MockLocalizationManager:
        def __init__(self, lang="en"): self.strings = {"en": {"config_token_label": "Discord Token (EN):", "config_save_button": "Save Config (EN)"}, "es": {"config_token_label": "Token Discord (ES):", "config_save_button": "Guardar Config (ES)"}}; self.current_lang = lang
        def get_string(self, key, **kwargs): return self.strings.get(self.current_lang, {}).get(key, key).format(**kwargs)
        def load_language(self, lang_code): self.current_lang = lang_code
    # Simular StateManager básico
    class MockStateManager:
         def __init__(self): self.loc_manager = MockLocalizationManager(); self.config = {"language": "en"}
         def save_configuration(self, data): print(f"MockStateManager: save_configuration called with {data}"); self.config.update(data); self.config_updated(); return True
         def config_updated(self): print("MockStateManager: Config Updated")

    mock_manager = MockStateManager()
    app = ctk.CTk()
    app.title("Test ConfigView")
    app.geometry("700x400")
    config_view = ConfigView(app, state_manager=mock_manager)
    config_view.pack(fill="both", expand=True, padx=10, pady=10)
    app.mainloop()