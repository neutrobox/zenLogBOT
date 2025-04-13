import os
import json
import threading
import datetime
import asyncio
from typing import Optional, Dict, List, Any, Callable, Tuple

# Importar clases necesarias con importación absoluta
from core.log_uploader import LogUploader # Cambiado
# from .models import LogUploadEntry # Ya no se usa
from core.discord_bot import DiscordBot # Cambiado
from core.localization import LocalizationManager # Cambiado
from core.utils import get_config_file_path # Cambiado

# Importar UI para type hinting (usando string para evitar importación circular real)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.app import App # Cambiado

class StateManager:
    """Gestiona el estado y la comunicación entre la UI y el core."""

    DEFAULT_CONFIG = {
        "language": "en",
        "discord_token": "",
        "target_channel_id": "",
        "log_folder_path": "",
        "dps_report_user_token": ""
    }

    def __init__(self):
        self.config_path = get_config_file_path()
        self.config = self._load_or_create_config()
        self.log_uploader = LogUploader(config=self.config)
        self.loc_manager = LocalizationManager(default_lang=self.config.get("language", "en"))
        self.ui_app: 'Optional[App]' = None # Usar string para type hint
        self.ui_logger: Callable[[str], None] = print
        self.discord_bot: Optional[DiscordBot] = None
        self.discord_bot_thread: Optional[threading.Thread] = None
        self._bot_start_lock = threading.Lock()
        self._boss_wing_map: Dict[str, Dict[str, str]] = self._build_boss_wing_map()

    def _load_or_create_config(self) -> Dict:
        """Carga config.json desde AppData o lo crea con valores por defecto."""
        print(f"StateManager: Loading config from: {self.config_path}")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    for key, value in self.DEFAULT_CONFIG.items(): loaded_config.setdefault(key, value)
                    print("StateManager: Config loaded successfully.")
                    return loaded_config
            except (json.JSONDecodeError, IOError, TypeError) as e:
                print(f"Error loading config file '{self.config_path}': {e}. Creating default config.")
                return self._create_default_config()
        else:
            print(f"Config file not found at '{self.config_path}'. Creating default config.")
            return self._create_default_config()

    def _create_default_config(self) -> Dict:
        """Crea y guarda un archivo de configuración por defecto en AppData."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f: json.dump(self.DEFAULT_CONFIG, f, indent=2)
            print(f"Default config created at: {self.config_path}")
            return self.DEFAULT_CONFIG.copy()
        except IOError as e:
            print(f"CRITICAL ERROR: Could not create default config file at '{self.config_path}': {e}")
            return self.DEFAULT_CONFIG.copy()

    def save_configuration(self, new_config_data: Dict):
        """Guarda el diccionario de configuración en el archivo JSON de AppData."""
        try:
            self.config.update(new_config_data)
            with open(self.config_path, 'w', encoding='utf-8') as f: json.dump(self.config, f, indent=2)
            self.log_to_ui(self.get_localized_string("config_status_saved"))
            print(f"Configuration saved to: {self.config_path}")
            self.config_updated()
            return True
        except IOError as e:
            error_msg = self.get_localized_string("config_status_error_save", error=e); self.log_to_ui(f"{self.get_localized_string('general_error')}: {error_msg}"); print(f"Error saving config: {e}"); return False
        except Exception as e:
            error_msg = self.get_localized_string("config_status_error_unexpected", error=e); self.log_to_ui(f"{self.get_localized_string('general_error')}: {error_msg}"); print(f"Unexpected error saving config: {e}"); return False

    def _build_boss_wing_map(self) -> Dict[str, Dict[str, str]]:
        """Crea un mapa {encounter_type: {boss_name: wing_key}} para búsqueda rápida."""
        mapping = {};
        for etype, wings in self.log_uploader.boss_definitions.items():
            mapping[etype] = {}
            for wing_key, bosses in wings.items():
                for boss_name in bosses.keys(): mapping[etype][boss_name] = wing_key
        return mapping

    def _get_wing_for_boss(self, encounter_type: str, boss_name: str) -> Optional[str]:
        """Obtiene la clave del ala/escala para un boss."""
        return self._boss_wing_map.get(encounter_type, {}).get(boss_name)

    def set_ui_app(self, ui_app_instance: 'App'): # Usar string para type hint
        """Establece la referencia a la instancia principal de la UI."""
        self.ui_app = ui_app_instance; self.load_config_into_ui(); self.update_ui_language(); self.start_discord_bot_if_configured()

    def set_ui_logger(self, logger_func: Callable[[str], None]):
        """Establece la función que se usará para loguear mensajes en la UI."""
        self.ui_logger = logger_func; self.log_to_ui(self.get_localized_string("log_idle", default="Idle."))

    def log_to_ui(self, message: str):
        """Envía un mensaje al logger de la UI (el CTkTextbox)."""
        print(f"UI LOG: {message}")
        try:
            if self.ui_app and self.ui_app.winfo_exists(): self.ui_app.after(0, self.ui_logger, message)
        except Exception as e: print(f"Error al intentar loguear en UI: {e}"); print(f"Mensaje original: {message}")

    def shutdown(self):
        """Realiza tareas de limpieza al cerrar la aplicación."""
        self.log_to_ui(self.get_localized_string("log_shutdown_starting", default="Initiating shutdown...")); self.stop_discord_bot(); self.log_to_ui(self.get_localized_string("log_shutdown_complete", default="Shutdown complete."))

    # --- Métodos llamados por la UI ---
    def config_updated(self):
        """Llamado internamente después de guardar la configuración."""
        self.log_uploader = LogUploader(config=self.config); self._boss_wing_map = self._build_boss_wing_map()
        new_lang = self.config.get("language", "en"); self.loc_manager.load_language(new_lang)
        self.update_ui_language(); self.stop_discord_bot(); self.start_discord_bot_if_configured()

    def load_config_into_ui(self):
        """Carga la configuración actual (desde self.config) en los campos de la UI."""
        if self.ui_app and hasattr(self.ui_app, 'config_frame'):
            config_view = self.ui_app.config_frame
            config_view.token_entry.delete(0, 'end'); config_view.token_entry.insert(0, self.config.get("discord_token", ""))
            config_view.channel_id_entry.delete(0, 'end'); config_view.channel_id_entry.insert(0, self.config.get("target_channel_id", ""))
            config_view.path_entry.delete(0, 'end'); config_view.path_entry.insert(0, self.config.get("log_folder_path", ""))
            config_view.dps_token_entry.delete(0, 'end'); config_view.dps_token_entry.insert(0, self.config.get("dps_report_user_token", ""))
            current_lang_code = self.config.get("language", "en"); current_lang_display = config_view.reverse_lang_map.get(current_lang_code, "English"); config_view.lang_combobox.set(current_lang_display)
            self.log_to_ui(self.get_localized_string("general_info") + ": Configuration loaded into UI.")

    def update_ui_language(self):
         """Actualiza todos los textos localizables en la UI."""
         if not self.ui_app: return
         self.log_to_ui(self.get_localized_string("log_lang_updating", lang=self.loc_manager.current_lang, default=f"Updating language to: {self.loc_manager.current_lang}"))
         self.ui_app.after(0, self._update_ui_language_threadsafe)

    def _update_ui_language_threadsafe(self):
        """Función auxiliar para actualizar la UI desde el hilo correcto."""
        if not self.ui_app or not self.ui_app.winfo_exists(): return
        lm = self.loc_manager; self.ui_app.title(lm.get_string("app_title"))
        if hasattr(self.ui_app, 'navigation_frame_label'): self.ui_app.navigation_frame_label.configure(text=lm.get_string("nav_header"))
        if hasattr(self.ui_app, 'select_button'): self.ui_app.select_button.configure(text=lm.get_string("nav_upload"))
        if hasattr(self.ui_app, 'config_button'): self.ui_app.config_button.configure(text=lm.get_string("nav_config"))
        if hasattr(self.ui_app, 'log_label'): self.ui_app.log_label.configure(text=lm.get_string("log_area_label"))
        if hasattr(self.ui_app, 'config_frame') and hasattr(self.ui_app.config_frame, 'update_language_display'): self.ui_app.config_frame.update_language_display(lm)
        if hasattr(self.ui_app, 'selection_frame') and hasattr(self.ui_app.selection_frame, 'update_language_display'): self.ui_app.selection_frame.update_language_display(lm)
        self.log_to_ui(self.get_localized_string("log_lang_updated", lang=self.loc_manager.current_lang, default=f"UI language updated to '{self.loc_manager.current_lang}'."))

    def get_localized_string(self, key: str, default: Optional[str] = None, **kwargs) -> str:
         """Método de conveniencia para obtener strings, con fallback opcional."""
         val = self.loc_manager.get_string(key, **kwargs)
         if val == key and default is not None:
             try: return default.format(**kwargs)
             except KeyError: return default
         return val

    def start_upload(self, selected_bosses: Dict[str, List[str]], show_duration: bool = False, upload_title: str = ""):
        """Inicia el proceso de subida de logs en un hilo separado."""
        lm = self.loc_manager
        if not self.discord_bot or not self.discord_bot.ready_event.is_set() or not self.discord_bot.is_ready():
             message = lm.get_string("upload_status_error_discord_disconnected"); self._update_ui_status(message, "red"); self.log_to_ui(f"{lm.get_string('general_error')}: {message}")
             if self.ui_app and hasattr(self.ui_app, 'selection_frame'): self.ui_app.after(0, lambda: self.ui_app.selection_frame.enable_upload_buttons()); return
        boss_list_str = ", ".join([f"{etype}: {', '.join(bl)}" for etype, bl in selected_bosses.items() if bl]); log_msg = self.get_localized_string("log_upload_starting", details=boss_list_str, default=f"Starting upload for: {boss_list_str}"); self.log_to_ui(log_msg)
        upload_thread = threading.Thread(target=self._upload_worker, args=(selected_bosses, show_duration, upload_title), daemon=True); upload_thread.start()

    # --- Gestión del Bot de Discord ---
    def start_discord_bot_if_configured(self):
        """Inicia el bot de Discord si el token y el ID del canal están configurados."""
        lm = self.loc_manager; config = self.config
        with self._bot_start_lock:
            if self.discord_bot and self.discord_bot.is_ready(): self.log_to_ui(lm.get_string("log_discord_already_ready", default="Discord bot already started and ready.")); return
            if self.discord_bot_thread and self.discord_bot_thread.is_alive(): self.log_to_ui(lm.get_string("log_discord_thread_running", default="Discord bot thread already running (likely connecting).")); return
            token = config.get("discord_token"); channel_id_str = config.get("target_channel_id")
            if not token: self.log_to_ui(lm.get_string("log_discord_error_token", default="Discord token not configured. Bot will not start.")); return
            if not channel_id_str: self.log_to_ui(lm.get_string("log_discord_error_channel_id", default="Channel ID not configured. Bot will not start.")); return
            try: channel_id = int(channel_id_str)
            except ValueError: msg = lm.get_string("config_status_error_channel_id_numeric"); self.log_to_ui(f"{lm.get_string('general_error')}: {msg}"); self._update_ui_status(msg, "red"); return
            self.log_to_ui(lm.get_string("log_discord_connecting", channel_id=channel_id, default=f"Starting Discord bot for channel {channel_id}..."))
            try:
                self.discord_bot = DiscordBot(token=token, target_channel_id=channel_id); self.discord_bot_thread = self.discord_bot.run_bot_in_thread()
                bot_ready = self.discord_bot.ready_event.wait(timeout=10.0); status_msg = ""; status_color = "orange"; log_msg = ""
                if bot_ready and self.discord_bot.is_ready(): status_msg = lm.get_string("discord_connection"); log_msg = f"{lm.get_string('general_info')}: {status_msg}"; status_color = "green"
                elif bot_ready: status_msg = lm.get_string("general_error") + ": " + lm.get_string("log_discord_start_error_suffix", default="Error starting Discord bot (see console)."); log_msg = status_msg; status_color = "red"
                else: status_msg = lm.get_string("general_warning") + ": " + lm.get_string("log_discord_connect_timeout_suffix", default="Timeout connecting Discord bot."); log_msg = status_msg; status_color = "orange"
                self.log_to_ui(log_msg); self._update_ui_status(status_msg, status_color)
            except Exception as e:
                error_msg = lm.get_string("log_discord_create_error_suffix", error=e, default=f"Error creating/starting Discord bot: {e}"); self.log_to_ui(error_msg); self._update_ui_status(lm.get_string("general_error") + f": {e}", "red"); self.discord_bot = None; self.discord_bot_thread = None

    def stop_discord_bot(self):
        """Detiene el bot de Discord si está corriendo."""
        lm = self.loc_manager
        with self._bot_start_lock:
            bot_loop = getattr(self.discord_bot, '_bot_loop', None) if self.discord_bot else None
            if bot_loop and bot_loop.is_running() and not bot_loop.is_closed():
                self.log_to_ui(lm.get_string("log_discord_closing", default="Requesting Discord bot shutdown..."))
                future = asyncio.run_coroutine_threadsafe(self.discord_bot.close_bot(), bot_loop)
                try: future.result(timeout=10)
                except asyncio.TimeoutError: self.log_to_ui(lm.get_string("log_discord_close_timeout_suffix", default="Timeout waiting for bot shutdown."))
                except RuntimeError as e:
                    if "Event loop is closed" in str(e): self.log_to_ui(lm.get_string("general_warning") + ": Loop already closed during shutdown.")
                    else: self.log_to_ui(lm.get_string("log_discord_close_unexpected_error_suffix", error=e, default=f"Unexpected runtime error during bot shutdown: {e}"))
                except asyncio.CancelledError: self.log_to_ui(lm.get_string("log_discord_close_expected_error_suffix", error_type="CancelledError", default="Expected error during bot shutdown (ignored): CancelledError"))
                except Exception as e: self.log_to_ui(lm.get_string("log_discord_close_unexpected_error_suffix", error=e, default=f"Unexpected error during bot shutdown: {e}"))
            elif self.discord_bot: self.log_to_ui(lm.get_string("general_warning") + ": Discord bot loop not running or closed, cannot schedule close.")
            if self.discord_bot_thread and self.discord_bot_thread.is_alive():
                self.log_to_ui(lm.get_string("log_discord_thread_joining", default="Waiting for Discord bot thread to finish..."))
                self.discord_bot_thread.join(timeout=5)
                if self.discord_bot_thread.is_alive(): self.log_to_ui(lm.get_string("log_discord_thread_join_timeout_suffix", default="Discord bot thread did not finish in time."))
            self.discord_bot = None; self.discord_bot_thread = None
            self.log_to_ui(lm.get_string("log_discord_resources_released", default="Discord bot resources released."))

    # --- Métodos internos y worker ---
    def _upload_worker(self, selected_bosses: Dict[str, List[str]], show_duration: bool, upload_title: str):
        """Trabajo de subida que se ejecuta en un hilo separado."""
        lm = self.loc_manager; total_bosses = sum(len(bl) for bl in selected_bosses.values()); processed_count = 0
        upload_results_for_embed: Dict[str, Dict[str, List[Dict]]] = {}; all_failures: List[Dict] = []
        for encounter_type, boss_list in selected_bosses.items():
            if encounter_type not in upload_results_for_embed: upload_results_for_embed[encounter_type] = {}
            for boss_name in boss_list:
                processed_count += 1; progress_message = lm.get_string("upload_status_processing", count=processed_count, total=total_bosses, boss=boss_name)
                self._update_ui_status(progress_message); self.log_to_ui(progress_message)
                latest_log = self.log_uploader.find_latest_log(boss_name, encounter_type); wing_key = self._get_wing_for_boss(encounter_type, boss_name) or "Unknown"
                result_data = {"boss_name": boss_name, "link": "", "success": False, "duration": None, "wing_key": wing_key, "message": ""}
                if not latest_log:
                    message = f"No se encontró log para {boss_name}"; status_msg = lm.get_string("upload_status_failed_log", message=message)
                    self._update_ui_status(status_msg, "orange"); self.log_to_ui(f"{lm.get_string('general_warning')}: {status_msg}")
                    result_data["success"] = False; result_data["message"] = message; all_failures.append(result_data); continue
                success, message, link = self.log_uploader.upload_log_to_dps_report(latest_log); duration = None
                if success and link and show_duration: duration = self.log_uploader.get_log_duration(link)
                status_color = "green" if success else "red"
                if success: final_message = lm.get_string("upload_status_uploaded_with_duration", boss=boss_name, duration=duration) if duration else lm.get_string("upload_status_uploaded", boss=boss_name)
                else: final_message = lm.get_string("upload_status_failed_log", message=message or "Error desconocido")
                self._update_ui_status(final_message, status_color); self.log_to_ui(final_message)
                result_data["link"] = link or ""; result_data["success"] = success; result_data["duration"] = duration; result_data["message"] = message if not success else ""
                if success:
                    if wing_key not in upload_results_for_embed[encounter_type]: upload_results_for_embed[encounter_type][wing_key] = []
                    upload_results_for_embed[encounter_type][wing_key].append(result_data)
                else: all_failures.append(result_data)
        completion_message = lm.get_string("upload_status_complete", total=total_bosses); self._update_ui_status(completion_message, "green"); self.log_to_ui(completion_message)
        bot_loop = getattr(self.discord_bot, '_bot_loop', None) if self.discord_bot else None
        if bot_loop and bot_loop.is_running() and not bot_loop.is_closed() and self.discord_bot.is_ready():
            discord_msg = lm.get_string("upload_status_sending_discord"); self._update_ui_status(discord_msg, "blue"); self.log_to_ui(discord_msg)
            final_embed_title = upload_title if upload_title else lm.get_string("embed_title_default")
            embed = self.discord_bot.format_embed(upload_results_for_embed, all_failures, loc_manager=lm, title_prefix=final_embed_title)
            if embed:
                future = asyncio.run_coroutine_threadsafe(self.discord_bot.send_embed_message(embed), bot_loop)
                try: send_success = future.result(timeout=15); discord_status = lm.get_string("upload_status_sent_discord") if send_success else lm.get_string("upload_status_error_discord_send"); color = "green" if send_success else "red"
                except asyncio.TimeoutError: discord_status = lm.get_string("upload_status_error_discord_timeout"); color = "red"
                except RuntimeError as e: discord_status = lm.get_string("general_error") + f" (loop cerrado?): {type(e).__name__}"; color = "red"
                except Exception as e: discord_status = lm.get_string("general_error") + f": {e}"; color = "red"
            else: discord_status = lm.get_string("upload_status_error_discord_format"); color = "orange"
        elif self.discord_bot and not self.discord_bot.is_ready(): discord_status = lm.get_string("upload_status_error_discord_not_ready"); color = "orange"
        else: discord_status = lm.get_string("upload_status_error_discord_disconnected"); color = "orange"
        self._update_ui_status(discord_status, color); self.log_to_ui(discord_status)
        if self.ui_app and hasattr(self.ui_app, 'selection_frame'): self.ui_app.after(0, lambda: self.ui_app.selection_frame.enable_upload_buttons())

    # --- Métodos para actualizar la UI ---
    def _update_ui_status(self, message: str, color: str = "gray"):
        """Actualiza la etiqueta de estado en la vista de selección."""
        if self.ui_app and hasattr(self.ui_app, 'selection_frame'):
            try:
                if self.ui_app.winfo_exists(): self.ui_app.after(0, self.ui_app.selection_frame.update_status, message, color)
            except Exception as e: print(f"Error actualizando etiqueta de estado UI (after): {e}")