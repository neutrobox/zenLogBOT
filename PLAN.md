# Plan para el Nuevo Bot de Logs con UI de Escritorio (`./nuevobot`)

1.  **Objetivo:** Crear una aplicación de escritorio (usando `CustomTkinter`) que interactúe con Discord para subir logs de ArcDPS a `dps.report`. Incluirá configuración de token y canal de Discord, selección visual de contenido, historial de subidas y publicación de resultados formateados (con emojis personalizados) en Discord.

2.  **Tecnologías Principales:**
    *   **Lenguaje:** Python 3.x
    *   **UI de Escritorio:** `CustomTkinter`
    *   **Interacción Discord:** `discord.py` (Necesario para usar emojis personalizados del servidor y enviar mensajes a un canal específico)
    *   **Subida de Logs:** `requests` (para la API de dps.report)
    *   **Manejo de Datos:** JSON o SQLite (para configuración, historial, definiciones de bosses)

3.  **Estructura de Directorios Propuesta (`./nuevobot`):**

    ```text
    nuevobot/
    ├── main.py             # Punto de entrada principal de la aplicación de escritorio
    ├── ui/                 # Módulos relacionados con la interfaz gráfica (CustomTkinter)
    │   ├── __init__.py
    │   ├── app.py          # Clase principal de la aplicación UI
    │   ├── views/          # Diferentes vistas/pantallas (config, selección, historial)
    │   │   ├── __init__.py
    │   │   ├── config_view.py
    │   │   ├── selection_view.py
    │   │   └── history_view.py
    │   └── widgets/        # Widgets personalizados si son necesarios
    │       └── __init__.py
    ├── core/               # Lógica central del bot (independiente de la UI)
    │   ├── __init__.py
    │   ├── discord_bot.py  # Lógica de conexión y envío de mensajes a Discord con discord.py
    │   ├── log_uploader.py # Lógica para encontrar y subir logs a dps.report
    │   ├── state_manager.py # Gestiona el estado entre UI y core (incluyendo el bot de Discord)
    │   └── models.py       # Modelos de datos (ej. LogEntry para historial)
    ├── data/               # Archivos de datos (configuración, historial, definiciones)
    │   ├── config.json     # Token, ID de canal, ruta de logs, etc.
    │   ├── history.db      # Base de datos SQLite para el historial (o history.json)
    │   └── boss_definitions.json # Similar a logs.json del bot original
    ├── assets/             # Iconos, imágenes para la UI
    │   └── icon.ico
    ├── requirements.txt    # Dependencias del proyecto
    └── README.md           # Documentación del nuevo bot
    ```

4.  **Componentes Principales y Flujo de Datos:**

    ```mermaid
    graph TD
        subgraph User Interface (CustomTkinter - ./ui/)
            UI_App[app.py: Ventana Principal]
            UI_ConfigView[views/config_view.py: Config Token/Canal/Ruta]
            UI_SelectionView[views/selection_view.py: Selección Boss/Alas]
            UI_HistoryView[views/history_view.py: Historial]
            UI_Progress[Widgets: Progreso Subida]
        end

        subgraph Core Logic (./core/)
            Core_StateManager[state_manager.py: Orquestador UI <-> Core]
            Core_LogUploader[log_uploader.py: Busca y Sube Logs]
            Core_DiscordBot[discord_bot.py: Conexión y Envío Discord]
            Core_Models[models.py: Estructuras de Datos]
        end

        subgraph Data Storage (./data/)
            Data_Config[config.json: Token, CanalID, Ruta]
            Data_History[history.db/json: Historial Subidas]
            Data_BossDefs[boss_definitions.json: Mapeo Bosses]
        end

        subgraph External Services
            API_DPSReport[dps.report API]
            API_Discord[Discord API]
        end

        UI_App --> Core_StateManager;
        UI_ConfigView -- Guarda/Lee --> Data_Config;
        UI_SelectionView -- Lee --> Data_BossDefs;
        UI_SelectionView -- Envía Selección --> Core_StateManager;
        UI_HistoryView -- Lee Historial --> Core_StateManager;

        Core_StateManager -- Inicia Subida --> Core_LogUploader;
        Core_StateManager -- Inicia Bot Discord --> Core_DiscordBot;
        Core_StateManager -- Envía Resultado Formateado --> Core_DiscordBot;
        Core_StateManager -- Actualiza UI --> UI_App;
        Core_StateManager -- Actualiza UI --> UI_Progress;

        Core_LogUploader -- Lee Config --> Data_Config;
        Core_LogUploader -- Lee Defs --> Data_BossDefs;
        Core_LogUploader -- Llama API --> API_DPSReport;
        Core_LogUploader -- Guarda Historial --> Data_History;
        Core_LogUploader -- Reporta Resultado --> Core_StateManager;

        Core_DiscordBot -- Lee Config --> Data_Config;
        Core_DiscordBot -- Interactúa --> API_Discord;
    ```

    *   La **UI (`./ui/`)** maneja la interacción con el usuario. `app.py` coordina las vistas. `config_view` ahora incluye el ID del canal de Discord.
    *   El **Core Logic (`./core/`)** contiene la funcionalidad principal. `state_manager.py` orquesta todo, incluyendo la inicialización y el uso de `discord_bot.py`. `log_uploader.py` se enfoca en la subida a dps.report. `discord_bot.py` maneja la conexión a Discord y el envío del mensaje formateado al canal especificado.
    *   **Data Storage (`./data/`)** almacena la configuración (incluyendo `target_channel_id`), el historial y las definiciones.
    *   El flujo principal: UI inicia subida -> `StateManager` -> `LogUploader` sube logs -> `LogUploader` reporta resultados a `StateManager` -> `StateManager` formatea resultados -> `StateManager` usa `DiscordBot` para enviar el embed formateado al canal configurado.

5.  **Dependencias Clave (requirements.txt):**
    *   `customtkinter`
    *   `discord.py`
    *   `requests`
    *   (Opcional) `pillow` (para imágenes en CustomTkinter)

6.  **Próximos Pasos (Implementación - Ajustados):**
    1.  ~~Crear la estructura de directorios y archivos iniciales.~~ (Hecho)
    2.  ~~Definir los modelos de datos (`./core/models.py`, `./data/config.json`, `./data/boss_definitions.json`).~~ (Hecho, `config.json` necesita ajuste)
    3.  ~~Implementar la lógica central de subida (`./core/log_uploader.py`), adaptando del bot original.~~ (Hecho)
    4.  ~~Desarrollar la estructura básica de la UI (`./ui/app.py`) con `CustomTkinter`.~~ (Hecho)
    5.  ~~Implementar las vistas individuales (configuración, selección, historial).~~ (Hecho, `config_view` necesita ajuste)
    6.  ~~Implementar el `state_manager` para conectar UI y Core.~~ (Hecho, necesita ajuste para `DiscordBot`)
    7.  **Actualizar `requirements.txt` para incluir `discord.py`.**
    8.  **Modificar `data/config.json` para añadir `target_channel_id`.**
    9.  **Modificar `ui/views/config_view.py` para configurar `target_channel_id`.**
    10. **Implementar `core/discord_bot.py` para conexión y envío de mensajes formateados.**
    11. **Modificar `core/state_manager.py` para inicializar y usar `discord_bot.py`.**
    12. Añadir manejo de errores y pruebas.