import requests
import os
import json
from typing import List, Dict, Optional, Tuple
import time # Para formatear duración
from .utils import get_bundled_data_path # Importar función de utils

DPS_REPORT_UPLOAD_ENDPOINT = 'https://b.dps.report/uploadContent?json=1&generator=ei'
DPS_REPORT_GET_JSON_ENDPOINT = 'https://b.dps.report/getJson' 

class LogUploader:
    """Gestiona la búsqueda y subida de logs de ArcDPS."""

    def __init__(self, config: Dict, defs_path_relative: str = "data/boss_definitions.json"):
        # Recibir config en lugar de cargarla
        self.config = config
        # Usar get_bundled_data_path para encontrar el archivo de definiciones
        self.defs_path = get_bundled_data_path(defs_path_relative)
        self.boss_definitions = self._load_json(self.defs_path)
        # Obtener log_folder_path desde la config recibida
        self.log_folder_path = self.config.get("log_folder_path", "")
        print(f"LogUploader: Using definitions path: {self.defs_path}")
        print(f"LogUploader: Using log folder path: {self.log_folder_path}")


    def _load_json(self, file_path: str) -> Dict:
        """Carga un archivo JSON."""
        # (La lógica de _load_json no necesita cambiar, solo se usa para defs ahora)
        try:
            if not os.path.exists(file_path):
                 print(f"Error: Definitions file not found - {file_path}")
                 return {} # Devolver vacío si no existe

            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found - {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format - {file_path}")
            return {}
        except IOError as e:
            print(f"Error I/O loading JSON - {file_path}: {e}")
            return {}


    def find_latest_log(self, boss_key: str, encounter_type: str = "raids") -> Optional[str]:
        """
        Encuentra la ruta del archivo de log más reciente para un boss específico,
        buscando en todas las alas/secciones del tipo de encuentro.
        """
        # (Lógica interna sin cambios, ya usa self.log_folder_path y self.boss_definitions)
        if not self.log_folder_path or not os.path.isdir(self.log_folder_path):
            print(f"Error: Log folder path not configured or invalid: {self.log_folder_path}")
            return None
        possible_folders = []; encounter_data = self.boss_definitions.get(encounter_type, {})
        for wing_key, wing_data in encounter_data.items():
            if boss_key in wing_data:
                possible_folders = wing_data[boss_key].get("name", []);
                if possible_folders: print(f"Definition found for {encounter_type}/{wing_key}/{boss_key}"); break
        if not possible_folders: print(f"Error: No folder definitions found for {encounter_type}/{boss_key}."); return None
        try:
            all_files = []; found_in_paths = set()
            for folder_name in possible_folders:
                boss_folder_path = os.path.normpath(os.path.join(self.log_folder_path, folder_name))
                if boss_folder_path in found_in_paths: continue
                if os.path.isdir(boss_folder_path):
                    print(f"Searching in: {boss_folder_path}"); found_in_paths.add(boss_folder_path)
                    for root, _, files in os.walk(boss_folder_path):
                        for file in files:
                            file_name, file_ext = os.path.splitext(file); file_ext_lower = file_ext.lower()
                            is_log_file = file_ext_lower in ['.zevtc', '.evtc'] or (file_ext_lower == '.zip' and file_name.lower().endswith('.evtc'))
                            if is_log_file:
                                file_path = os.path.join(root, file)
                                try: modified_date = os.path.getmtime(file_path); all_files.append((file_path, modified_date))
                                except FileNotFoundError: print(f"Warning: File {file_path} not found during getmtime."); continue
            if not all_files: print(f"No valid log files found for {boss_key}."); return None
            all_files.sort(key=lambda x: x[1], reverse=True); latest_log_path = all_files[0][0]
            print(f"Latest log found for {boss_key}: {latest_log_path}"); return latest_log_path
        except Exception as e: print(f"Unexpected error finding logs for {boss_key}: {e}"); import traceback; traceback.print_exc(); return None


    def upload_log_to_dps_report(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        Sube un archivo de log a dps.report.
        """
        if not os.path.exists(file_path): return False, f"File not found: {file_path}", None
        print(f"Uploading {os.path.basename(file_path)} to {DPS_REPORT_UPLOAD_ENDPOINT}...")
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}; params = {}
                user_token = self.config.get('dps_report_user_token')
                if user_token: params['userToken'] = user_token
                res = requests.post(DPS_REPORT_UPLOAD_ENDPOINT, files=files, params=params, timeout=300)

            if res.status_code == 200:
                try:
                    json_data = res.json(); permalink = json_data.get('permalink')
                    if permalink: print(f"Upload successful: {permalink}"); return True, "Upload successful.", permalink
                    else: error_msg = json_data.get('error', 'Unexpected JSON response (no permalink)'); print(f"Upload error (JSON): {error_msg}"); return False, f"dps.report error: {error_msg}", None
                except ValueError: print(f"Error: Could not decode JSON response. Code: {res.status_code}, Response: {res.text[:200]}"); return False, "Error decoding dps.report response.", None
            elif res.status_code == 429: # Rate limit
                 print(f"Error: Rate limit exceeded. Response: {res.text[:200]}")
                 error_msg = 'Rate limit exceeded.'
                 try:
                     # Intentar obtener mensaje de error específico del JSON
                     error_data = res.json()
                     error_msg = error_data.get('error', error_msg)
                 except ValueError:
                     pass # Mantener mensaje genérico si la respuesta no es JSON
                 return False, error_msg, None
            else: print(f"Upload error: Status code {res.status_code}, Response: {res.text[:200]}"); return False, f"HTTP error {res.status_code} during upload.", None
        except requests.exceptions.Timeout: print("Error: Timeout during upload."); return False, "Timeout during upload.", None
        except requests.exceptions.RequestException as e: print(f"Network error during upload: {e}"); return False, f"Network error: {e}", None
        except Exception as e: print(f"Unexpected error during upload: {e}"); import traceback; traceback.print_exc(); return False, f"Unexpected error: {e}", None

    def get_log_duration(self, permalink: str) -> Optional[str]:
        """
        Obtiene la duración de un log desde dps.report usando el endpoint getJson.
        """
        # (Lógica interna sin cambios)
        if not permalink: return None
        print(f"Fetching duration for: {permalink}")
        try:
            params = {'permalink': permalink}; res = requests.get(DPS_REPORT_GET_JSON_ENDPOINT, params=params, timeout=60)
            if res.status_code == 200:
                try:
                    json_data = res.json(); duration_str = json_data.get('duration')
                    if duration_str:
                         try: duration_seconds = float(duration_str); minutes = int(duration_seconds // 60); seconds = duration_seconds % 60; formatted_duration = f"{minutes:02d}:{seconds:06.3f}"; print(f"Duration fetched: {formatted_duration}"); return formatted_duration
                         except ValueError: print(f"Duration fetched (original format): {duration_str}"); return duration_str
                    else: print("Error: 'duration' not found in getJson response."); return None
                except ValueError: print(f"Error: Could not decode getJson response. Code: {res.status_code}, Response: {res.text[:200]}"); return None
            else: print(f"Error fetching JSON: Status code {res.status_code}, Response: {res.text[:200]}"); return None
        except requests.exceptions.Timeout: print("Error: Timeout fetching duration JSON."); return None
        except requests.exceptions.RequestException as e: print(f"Network error fetching duration JSON: {e}"); return None
        except Exception as e: print(f"Unexpected error fetching duration: {e}"); import traceback; traceback.print_exc(); return None


# --- Ejemplo de uso (para pruebas) ---
if __name__ == '__main__':
    # Cargar config dummy para prueba
    mock_config = {"log_folder_path": "RUTA/A/TUS/LOGS", "dps_report_user_token": ""} # PON UNA RUTA REAL AQUÍ
    # Ruta relativa a boss_definitions desde este archivo
    defs_rel_path = "../data/boss_definitions.json"

    uploader = LogUploader(config=mock_config, defs_path_relative=defs_rel_path)

    if not uploader.log_folder_path or uploader.log_folder_path == "RUTA/A/TUS/LOGS":
        print("Please set a real 'log_folder_path' in the mock_config in the script for testing.")
    else:
        boss_to_find = "Vale Guardian"; encounter_t = "raids"
        print(f"\n--- Finding log for {boss_to_find} ({encounter_t}) ---")
        latest_log = uploader.find_latest_log(boss_to_find, encounter_t)
        if latest_log:
             print(f"\n--- Uploading log: {latest_log} ---")
             success, message, link = uploader.upload_log_to_dps_report(latest_log)
             print(f"\n--- Upload Result ---"); print(f"Success={success}\nMessage='{message}'\nLink={link}")
             if success and link:
                  print(f"\n--- Fetching duration for {link} ---")
                  duration = uploader.get_log_duration(link)
                  print(f"\n--- Duration Result ---"); print(f"Duration: {duration if duration else 'Not available'}")
        else: print(f"\nCould not find log for {boss_to_find} to test upload.")