import json
import os
import sys
from typing import Dict, Optional
from .utils import get_bundled_data_path # Importar función de utils

class LocalizationManager:
    """Gestiona la carga y el acceso a las cadenas de texto localizadas."""

    def __init__(self, lang_dir_name: str = "lang", data_dir_name: str = "data", default_lang: str = "en"):
        self.lang_dir_name = lang_dir_name
        self.data_dir_name = data_dir_name
        self.default_lang = default_lang
        self.current_lang = default_lang
        self.strings: Dict[str, str] = {}
        # Usar get_bundled_data_path para encontrar el directorio lang
        self.lang_dir = get_bundled_data_path(os.path.join(self.data_dir_name, self.lang_dir_name))
        print(f"LocalizationManager: Using language directory: {self.lang_dir}")
        self.load_language(self.current_lang)

    # _get_base_path ya no es necesario aquí

    def _load_json(self, file_path: str) -> Optional[Dict[str, str]]:
        """Carga un archivo JSON de idioma."""
        if not os.path.exists(file_path):
            print(f"Error: Language file not found - {file_path}")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading language file {file_path}: {e}")
            return None

    def load_language(self, lang_code: str):
        """Carga las cadenas para un código de idioma específico."""
        print(f"Loading language: {lang_code}")
        file_path = os.path.join(self.lang_dir, f"{lang_code}.json")
        loaded_strings = self._load_json(file_path)

        if loaded_strings is not None:
            self.strings = loaded_strings
            self.current_lang = lang_code
            print(f"Language '{lang_code}' loaded successfully.")
        else:
            print(f"Failed to load language '{lang_code}'. Attempting to load default '{self.default_lang}'.")
            if lang_code != self.default_lang:
                default_file_path = os.path.join(self.lang_dir, f"{self.default_lang}.json")
                default_strings = self._load_json(default_file_path)
                if default_strings is not None:
                    self.strings = default_strings
                    self.current_lang = self.default_lang
                    print(f"Default language '{self.default_lang}' loaded as fallback.")
                else:
                    print(f"Critical Error: Could not load requested language or default language.")
                    self.strings = {}
                    self.current_lang = ""
            else:
                 self.strings = {}
                 self.current_lang = ""


    def get_string(self, key: str, **kwargs) -> str:
        """
        Obtiene una cadena localizada por su clave.
        Permite formatear la cadena usando kwargs.
        Devuelve la clave si no se encuentra la cadena.
        """
        string_template = self.strings.get(key, key) # Devolver clave si no existe
        try:
            return string_template.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Missing format argument '{e}' for key '{key}' in language '{self.current_lang}'")
            return string_template # Devolver sin formatear si faltan args
        except Exception as e:
             print(f"Error formatting string for key '{key}': {e}")
             return string_template # Devolver sin formatear en otros errores


# --- Ejemplo de uso ---
if __name__ == "__main__":
    # Crear archivos dummy si no existen (relativo a este script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_d = os.path.join(os.path.dirname(script_dir), "data") # Ruta a nuevobot/data
    lang_d = os.path.join(data_d, "lang")

    if not os.path.exists(lang_d): os.makedirs(lang_d)
    en_path = os.path.join(lang_d, "en.json")
    es_path = os.path.join(lang_d, "es.json")
    if not os.path.exists(en_path):
        with open(en_path, "w") as f: json.dump({"hello": "Hello {name}!", "config_save_button": "Save Config"}, f)
    if not os.path.exists(es_path):
         with open(es_path, "w") as f: json.dump({"hello": "¡Hola {name}!", "config_save_button": "Guardar Config"}, f)


    print("--- Testing English (default) ---")
    # Pasar solo los nombres relativos de directorio
    loc_manager = LocalizationManager(lang_dir_name="lang", data_dir_name="data", default_lang="en")
    print(f"Using lang_dir: {loc_manager.lang_dir}")
    print(loc_manager.get_string("hello", name="World"))
    print(loc_manager.get_string("config_save_button"))
    print(loc_manager.get_string("non_existent_key"))

    print("\n--- Testing Spanish ---")
    loc_manager.load_language("es")
    print(loc_manager.get_string("hello", name="Mundo"))
    print(loc_manager.get_string("config_save_button"))

    print("\n--- Testing Fallback to English ---")
    loc_manager.load_language("fr") # Non-existent language
    print(loc_manager.get_string("hello", name="Monde")) # Should show English
    print(loc_manager.get_string("config_save_button")) # Should show English