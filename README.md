# zenLogBOT - GW2 Log Uploader

A desktop application to upload Guild Wars 2 ArcDPS logs to [dps.report] and post formatted results to Discord.

## Features

*   **Graphical User Interface:** Built with CustomTkinter for a modern look.
*   **Upload to dps.report:** Uploads `.evtc`, `.zevtc`, and `.evtc.zip` files to the `b.dps.report` endpoint.
*   **Discord Publishing:**
    *   Sends a formatted *embed* message to the specified Discord channel.
    *   Groups logs by Wing/Scale/Section.
    *   Displays the boss name in bold as a link to the report.
    *   Uses custom emojis from the Discord server (if the bot is a member).
    *   Option to display encounter duration.
    *   Allows adding a custom title to each upload batch.
*   **Flexible Selection:**
    *   **Presets:** Buttons for quick uploads (Full Raid Clear W1-W8, Semi FC W1-W7, All Fractal CMs).
    *   **By Category:** Buttons to show and select specific logs for Raids, Strikes, or Fractals.
*   **Persistent Configuration:** Saves settings (token, channel, path, language, etc.) in the user's data folder (`%APPDATA%\zenLogBOT` on Windows).
*   **Operation Log:** Displays progress and results directly in the UI.
*   **Multi-language:** Interface available in English and Spanish.
*   **Custom Icon:** Uses `favicon.ico`.
*   **Automatic Centering:** Main window and dialogs appear centered.

## Installation and Execution (from Source Code)

These instructions are for running the application directly from the source code, ideal for development or if you prefer not to use the pre-compiled executable.

1.  **Prerequisites:**
    *   [Python](https://www.python.org/downloads/) (version 3.11+ recommended). Ensure `python` and `pip` are in your PATH.
    *   [Git](https://git-scm.com/downloads/).

2.  **Clone the Repository:**
    ```bash
    # Navigate to the folder where you want to clone the project
    git clone <REPOSITORY_URL> gw2logbot
    cd gw2logbot
    ```

3.  **Create and Activate Virtual Environment (Recommended):**
    This creates an isolated environment for the project's dependencies, avoiding conflicts with other Python projects.
    ```bash
    # Inside the gw2logbot folder
    python -m venv venv
    # Activate the virtual environment:
    # Windows (cmd/powershell):
    .\venv\Scripts\activate
    # Linux/macOS (bash/zsh):
    source venv/bin/activate
    ```
    *(You will see `(venv)` at the beginning of your command line if it's active).*

4.  **Install Dependencies:**
    With the virtual environment activated, install the necessary libraries:
    ```bash
    pip install -r ./nuevobot/requirements.txt
    ```

5.  **Run the Application:**
    ```bash
    python ./nuevobot/main.py
    ```

6.  **Initial Configuration:**
    *   The first time you run, go to the "Configuration" tab.
    *   Enter your **Discord bot Token**.
    *   Enter the **Discord Channel ID** where you want logs to be posted.
    *   Select your **Logs Folder** (`arcdps.cbtlogs`) using the "Browse..." button.
    *   (Optional) Enter your dps.report user token.
    *   Select the desired language.
    *   Click "Save configuration".
    *   **Restart the application** for the Discord bot to connect correctly with the new settings.

7.  **Usage:**
    *   Go to the "Upload logs" tab.
    *   Use the **Preset** buttons or select a **Category** to choose specific logs.
    *   Optionally, check "Show encounter duration".
    *   Click the corresponding upload button ("Full Raid Clear", "Upload selected", etc.).
    *   Enter an optional title in the pop-up window.
    *   Observe the progress in the "Log Output" area.
    *   The formatted results will be posted to the configured Discord channel.

8.  **Deactivate Virtual Environment:**
    When you are finished using the application, you can deactivate the virtual environment:
    ```bash
    deactivate
    ```

## Manual Executable Build (Optional)

If you wish to create your own standalone `.exe` file:

1.  **Follow steps 1-4 from "Installation and Execution (from Source Code)"** to set up the virtual environment and install base dependencies.
2.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```
3.  **Run PyInstaller:**
    From the root project folder (`gw2logbot`), run the following command:
    ```bash
    pyinstaller --name "zenLogBOT" --onefile --windowed --icon="./nuevobot/favicon.ico" --add-data="./nuevobot/data;data" ./nuevobot/main.py
    ```
    *   `--onedir`: Alternatively, you can use `--onedir` instead of `--onefile`. This will create a folder in `dist` instead of a single file, which is less likely to be flagged as a false positive by antivirus software. If you use `--onedir`, you must distribute the entire generated folder found inside `dist`.
4.  **Result:** The executable (`zenLogBOT.exe`) or folder (`dist/zenLogBOT`) will be located in the `dist` folder.

## Project Structure

See `PLAN.md` for the detailed project structure.