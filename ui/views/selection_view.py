import customtkinter as ctk
import json
import os
import sys # Importar sys para la ruta del icono
from typing import Dict, List, TYPE_CHECKING, Optional

# Importar state manager y utils con importación absoluta
if TYPE_CHECKING:
    from core.state_manager import StateManager # Cambiado
from core.utils import get_bundled_data_path # Cambiado

class SelectionView(ctk.CTkFrame):
    """Vista para la selección visual de bosses/alas a subir."""

    def __init__(self, master, state_manager: 'Optional[StateManager]' = None):
        super().__init__(master)
        self.state_manager = state_manager
        self.boss_definitions = {}
        if self.state_manager and hasattr(self.state_manager, 'log_uploader'):
            self.boss_definitions = self.state_manager.log_uploader.boss_definitions
        else:
            print("ERROR: StateManager o LogUploader no disponible en SelectionView para obtener definiciones.")

        self.checkbox_vars: Dict[str, Dict[str, Dict[str, ctk.BooleanVar]]] = {}
        self.lm = self.state_manager.loc_manager if self.state_manager else None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0); self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0); self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=0); self.grid_rowconfigure(5, weight=0)

        # --- Título ---
        self.title_label = ctk.CTkLabel(self, text=self.get_string("upload_title"), font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        # --- Frame de Presets ---
        self.presets_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.presets_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.presets_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.presets_label = ctk.CTkLabel(self.presets_frame, text=self.get_string("upload_presets_label"))
        self.presets_label.grid(row=0, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="w")
        self.preset_raid_fc_all_button = ctk.CTkButton(self.presets_frame, text=self.get_string("upload_preset_raid_fc_all"), command=lambda: self.start_preset_upload("raid_fc_all"))
        self.preset_raid_fc_all_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.preset_raid_fc7_button = ctk.CTkButton(self.presets_frame, text=self.get_string("upload_preset_raid_fc_7"), command=lambda: self.start_preset_upload("raid_fc_7"))
        self.preset_raid_fc7_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.preset_fractal_button = ctk.CTkButton(self.presets_frame, text=self.get_string("upload_preset_fractal_cms"), command=lambda: self.start_preset_upload("fractal_cms"))
        self.preset_fractal_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # --- Frame de Selección Específica por Categoría ---
        self.specific_category_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.specific_category_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.specific_category_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.specific_label = ctk.CTkLabel(self.specific_category_frame, text=self.get_string("upload_specific_label"))
        self.specific_label.grid(row=0, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="w")
        self.specific_raid_button = ctk.CTkButton(self.specific_category_frame, text=self.get_string("upload_specific_raid_button"), command=lambda: self.show_specific_selection("raids"))
        self.specific_raid_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.specific_strike_button = ctk.CTkButton(self.specific_category_frame, text=self.get_string("upload_specific_strike_button"), command=lambda: self.show_specific_selection("strikes"))
        self.specific_strike_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.specific_fractal_button = ctk.CTkButton(self.specific_category_frame, text=self.get_string("upload_specific_fractal_button"), command=lambda: self.show_specific_selection("fractals"))
        self.specific_fractal_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # --- Frame de Selección Detallada (Scrollable, inicialmente oculto) ---
        self.specific_detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.specific_detail_frame.grid_columnconfigure(0, weight=1)
        self.specific_detail_frame.grid_rowconfigure(0, weight=1)
        self.scrollable_frame = ctk.CTkScrollableFrame(self.specific_detail_frame, label_text=self.get_string("upload_scrollframe_label"))
        self.scrollable_frame.grid(row=0, column=0, padx=0, pady=(5, 10), sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.specific_upload_button = ctk.CTkButton(self.specific_detail_frame, text=self.get_string("upload_specific_upload_button"), command=self.start_specific_upload_action)
        self.specific_upload_button.grid(row=1, column=0, padx=0, pady=5, sticky="ew")

        # --- Checkbox Duración ---
        self.duration_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.duration_frame.grid(row=4, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.show_duration_var = ctk.BooleanVar(value=False)
        self.duration_checkbox = ctk.CTkCheckBox(self.duration_frame, text=self.get_string("upload_show_duration_checkbox"), variable=self.show_duration_var)
        self.duration_checkbox.grid(row=0, column=0, padx=0, pady=5, sticky="w")

        # --- Etiqueta de Estado/Progreso ---
        self.status_label = ctk.CTkLabel(self, text=self.get_string("upload_status_idle"), text_color="gray", wraplength=700)
        self.status_label.grid(row=5, column=0, padx=10, pady=(5, 10), sticky="ew")

        self.specific_detail_frame_visible = False

    def show_specific_selection(self, category_filter: Optional[str] = None):
        """Muestra el frame de selección detallada, filtrado opcionalmente."""
        print(f"Mostrando selección específica para: {category_filter if category_filter else 'Todo'}")
        self._populate_checkboxes(category_filter)
        if not self.specific_detail_frame_visible:
            self.specific_detail_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
            self.duration_frame.grid(row=4, column=0, padx=10, pady=(10, 0), sticky="ew")
            self.status_label.grid(row=5, column=0, padx=10, pady=(5, 10), sticky="ew")
            self.specific_detail_frame_visible = True

    def get_string(self, key: str, **kwargs) -> str:
        """Obtiene la cadena localizada o la clave si falla."""
        if self.lm: return self.lm.get_string(key, **kwargs)
        return key

    def _populate_checkboxes(self, category_filter: Optional[str] = None):
        """Llena el frame scrollable con checkboxes, opcionalmente filtrados."""
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.checkbox_vars = {}
        current_row = 0
        for encounter_type, wings in self.boss_definitions.items():
            if category_filter and encounter_type != category_filter: continue
            type_label = ctk.CTkLabel(self.scrollable_frame, text=encounter_type.capitalize(), font=ctk.CTkFont(weight="bold"))
            type_label.grid(row=current_row, column=0, padx=5, pady=(10, 2), sticky="w")
            current_row += 1; self.checkbox_vars[encounter_type] = {}
            for wing_name, bosses in wings.items():
                wing_label = ctk.CTkLabel(self.scrollable_frame, text=f"  {wing_name}:")
                wing_label.grid(row=current_row, column=0, padx=15, pady=2, sticky="w")
                current_row += 1; self.checkbox_vars[encounter_type][wing_name] = {}
                for boss_name in bosses.keys():
                    var = ctk.BooleanVar()
                    checkbox = ctk.CTkCheckBox(self.scrollable_frame, text=boss_name, variable=var)
                    checkbox.grid(row=current_row, column=0, padx=30, pady=1, sticky="w")
                    self.checkbox_vars[encounter_type][wing_name][boss_name] = var; current_row += 1
        print(f"Checkboxes poblados para filtro: {category_filter}")

    def get_selected_logs(self) -> Dict[str, List[str]]:
        """Obtiene un diccionario de los bosses seleccionados de los checkboxes."""
        selected = {}
        for encounter_type, wings in self.checkbox_vars.items():
            selected_in_type = []
            for wing_name, bosses in wings.items():
                for boss_name, var in bosses.items():
                    if var.get(): selected_in_type.append(boss_name)
            if selected_in_type: selected[encounter_type] = selected_in_type
        return selected

    def _get_preset_boss_list(self, preset_key: str) -> Dict[str, List[str]]:
        """Construye la lista de bosses para un preset dado."""
        preset_selection = {}
        if preset_key == "raid_fc_all":
            preset_selection["raids"] = []
            raid_defs = self.boss_definitions.get("raids", {})
            for wing in ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"]:
                if wing in raid_defs: preset_selection["raids"].extend(raid_defs[wing].keys())
        elif preset_key == "raid_fc_7":
             preset_selection["raids"] = []
             raid_defs = self.boss_definitions.get("raids", {})
             for wing in ["W1", "W2", "W3", "W4", "W5", "W6", "W7"]:
                 if wing in raid_defs: preset_selection["raids"].extend(raid_defs[wing].keys())
        elif preset_key == "fractal_cms":
            preset_selection["fractals"] = []
            fractal_defs = self.boss_definitions.get("fractals", {})
            for scale in fractal_defs:
                 if scale.endswith("CM"): preset_selection["fractals"].extend(fractal_defs[scale].keys())
        elif preset_key == "strikes":
             preset_selection["strikes"] = []
             strike_defs = self.boss_definitions.get("strikes", {})
             for section in strike_defs:
                 preset_selection["strikes"].extend(strike_defs[section].keys())
        return preset_selection

    def _ask_title_and_start_upload(self, boss_selection: Dict[str, List[str]]):
        """Función auxiliar para pedir título e iniciar subida."""
        if not any(boss_selection.values()):
            self.update_status(self.get_string("upload_status_no_selection"), "orange")
            return
        show_duration = self.show_duration_var.get()
        dialog = ctk.CTkInputDialog(text=self.get_string("upload_ask_title_dialog_text"), title=self.get_string("upload_ask_title_dialog_title"))
        try:
            dialog.update_idletasks(); dialog_width = dialog.winfo_width(); dialog_height = dialog.winfo_height()
            screen_width = dialog.winfo_screenwidth(); screen_height = dialog.winfo_screenheight()
            x = (screen_width / 2) - (dialog_width / 2); y = (screen_height / 2) - (dialog_height / 2)
            dialog.geometry(f"+{int(x)}+{int(y)}")
            icon_path = get_bundled_data_path("favicon.ico") # Usar función importada
            if os.path.exists(icon_path): dialog.iconbitmap(icon_path); print(f"Icono establecido para diálogo desde: {icon_path}")
            else: print(f"Advertencia: Icono no encontrado para diálogo en {icon_path}")
        except Exception as e: print(f"Error al centrar o establecer icono del diálogo: {e}")
        upload_title = dialog.get_input()
        if upload_title is None: print("Subida cancelada por el usuario."); return
        upload_title = upload_title.strip()
        self.update_status(self.get_string("upload_status_starting"), "gray")
        self.disable_upload_buttons()
        if self.state_manager: self.state_manager.start_upload(boss_selection, show_duration=show_duration, upload_title=upload_title)
        else: self.update_status(self.get_string("upload_status_error_state_manager"), "red"); self.enable_upload_buttons()

    def start_preset_upload(self, preset_key: str):
        """Manejador para botones de preset."""
        print(f"Iniciando preset: {preset_key}")
        boss_selection = self._get_preset_boss_list(preset_key)
        self._ask_title_and_start_upload(boss_selection)

    def start_specific_upload_action(self):
        """Manejador para el botón 'Subir Seleccionados'."""
        print("Iniciando subida específica...")
        boss_selection = self.get_selected_logs()
        self._ask_title_and_start_upload(boss_selection)

    def disable_upload_buttons(self):
        """Deshabilita todos los botones que inician una subida."""
        self.preset_raid_fc_all_button.configure(state="disabled"); self.preset_raid_fc7_button.configure(state="disabled")
        self.preset_fractal_button.configure(state="disabled"); self.specific_raid_button.configure(state="disabled")
        self.specific_strike_button.configure(state="disabled"); self.specific_fractal_button.configure(state="disabled")
        self.specific_upload_button.configure(state="disabled")

    def enable_upload_buttons(self):
        """Habilita todos los botones de subida."""
        self.preset_raid_fc_all_button.configure(state="normal"); self.preset_raid_fc7_button.configure(state="normal")
        self.preset_fractal_button.configure(state="normal"); self.specific_raid_button.configure(state="normal")
        self.specific_strike_button.configure(state="normal"); self.specific_fractal_button.configure(state="normal")
        self.specific_upload_button.configure(state="normal")

    def update_status(self, message: str, color: str = "gray"):
        """Actualiza la etiqueta de estado y reactiva botones si es un estado final."""
        self.status_label.configure(text=message, text_color=color)
        if color != "gray" and color != "blue": self.enable_upload_buttons()

    def update_language_display(self, loc_manager):
        """Actualiza los textos de esta vista."""
        self.lm = loc_manager
        self.title_label.configure(text=self.get_string("upload_title"))
        self.presets_label.configure(text=self.get_string("upload_presets_label"))
        self.preset_raid_fc_all_button.configure(text=self.get_string("upload_preset_raid_fc_all"))
        self.preset_raid_fc7_button.configure(text=self.get_string("upload_preset_raid_fc_7"))
        self.preset_fractal_button.configure(text=self.get_string("upload_preset_fractal_cms"))
        self.specific_label.configure(text=self.get_string("upload_specific_label"))
        self.specific_raid_button.configure(text=self.get_string("upload_specific_raid_button"))
        self.specific_strike_button.configure(text=self.get_string("upload_specific_strike_button"))
        self.specific_fractal_button.configure(text=self.get_string("upload_specific_fractal_button"))
        self.specific_upload_button.configure(text=self.get_string("upload_specific_upload_button"))
        self.scrollable_frame.configure(label_text=self.get_string("upload_scrollframe_label"))
        self.duration_checkbox.configure(text=self.get_string("upload_show_duration_checkbox"))

# --- Para pruebas directas de esta vista ---
if __name__ == "__main__":
    pass # Deshabilitar prueba directa por complejidad