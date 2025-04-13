# zenLogBOT - GW2 Log Uploader

A desktop application to upload Guild Wars 2 ArcDPS logs to [dps.report] and post formatted results to Discord.

## Features

*   **Upload to dps.report:** Uploads `.evtc`, `.zevtc`, and `.evtc.zip` files to the `b.dps.report` endpoint.
*   **Discord Publishing:**
    *   Sends a formatted *embed* message to the specified Discord channel.
    *   Groups logs by Wing/Scale (Fractals)/Strikes.
    *   Option to display encounter duration in the Discord message sent.
    *   Allows adding a custom title to each upload batch (Discord message).
*   **Flexible selection:**
    *   **Presets:** Buttons for quick uploads (Full Raid Clear W1-W8, Semi FC W1-W7, All Fractal CMs).
    *   **By category:** Buttons to show and select specific logs for Raids, Strikes, or Fractals.
*   **Persistent configuration:** Saves settings (token, channel, path, language, etc.) in the user's data folder (`%APPDATA%\zenLogBOT` on Windows).
*   **Multi-language:** Interface available in English and Spanish.

## Installation and execution (from source code)

These instructions are for running the application directly from the source code, if you prefer not to use the pre-compiled executable.

1.  **Prerequisites:**
    *   [Python](https://www.python.org/downloads/) (version 3.11+ recommended). Ensure `python` and `pip` are in your PATH.
    *   [Git](https://git-scm.com/downloads/).

2.  **Clone the repository:**
    ```bash
    # Navigate to the folder where you want to clone the project
    git clone https://github.com/neutrobox/zenLogBOT.git
    cd zenLogBOT
    ```

3.  **Create and activate Virtual Environment (Recommended):**
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
    pip install -r requirements.txt
    ```

5.  **Run the Application:**
    ```bash
    python main.py
    ```

6.  **Initial Configuration:**
    *   The first time you run, go to the "Configuration" tab.
    *   Enter your **Discord BOT Token**. (Tutorial on how to create a Discord BOT and retrieve it's token: [here](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token))
    *   Enter the **Discord Channel ID** where you want logs to be posted.
    *   Select your **Logs folder** (`arcdps.cbtlogs`) using the "Browse..." button.
    *   (Optional) Enter your dps.report user token.
    *   Select the desired language.
    *   Click "Save configuration".
    *   **Restart the application** for the Discord bot to connect correctly with the new settings.

7.  **Usage:**
    *   Go to the "Upload logs" tab.
    *   Optionally, check "Show encounter duration" to display the encounter duration in the message sent to the Discord channel configured previously.
    *   Use the **Preset** buttons or select a **Category** to choose specific logs.
    *   Enter an optional title in the pop-up window and click 
    *   Observe the progress in the "Output" area.
    *   The formatted results will be posted to the configured Discord channel.

8.  **Deactivate Virtual Environment:**
    When you are finished using the application, you can deactivate the virtual environment:
    ```bash
    deactivate
    ```

## Manual executable build (Optional)

If you wish to create your own standalone `.exe` file:

1.  **Follow steps 1-4 from "Installation and Execution (from Source Code)"** to set up the virtual environment and install base dependencies.
2.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```
3.  **Run PyInstaller:**
    From the root project folder (`gw2logbot`), run the following command:
    ```bash
    pyinstaller --name "zenLogBOT" --onefile --windowed --icon="favicon.ico" --add-data="data;data" main.py
    ```
    *   `--onedir`: Alternatively, you can use `--onedir` instead of `--onefile`. This will create a folder in `dist` instead of a single file, which is less likely to be flagged as a false positive by antivirus software.
4.  **Result:** The executable (`zenLogBOT.exe`) or folder (`dist/zenLogBOT`) will be located in the `dist` folder.