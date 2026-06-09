# Zoom & Screen Recorder for Linux (Wayland / GNOME)

A lightweight, high-efficiency screen and system audio recorder for Linux (GNOME/Wayland). This modular Python application features both an automatic recording daemon that triggers upon detecting Zoom calls, and a native Graphical User Interface (GUI) for manual full-screen capture. It applies advanced post-processing compression settings to ensure maximum text and slide readability while using minimal disk space.

---

## 📂 Project Directory Structure

The project is designed with a clean, modular, and decoupled Object-Oriented structure:

*   **[main.py](file:///home/cristina/Documentos/grabarPantalla/main.py)**: The main terminal orchestrator (`ZoomRecorderApp`) running the Zoom polling loop and daemon.
*   **[gui.py](file:///home/cristina/Documentos/grabarPantalla/gui.py)**: The native GTK 3 Graphical User Interface (GUI) to visually trigger recordings, select modes, and monitor elapsed time.
*   **[install.py](file:///home/cristina/Documentos/grabarPantalla/install.py)**: The installation script that configures the launcher shortcut on your Desktop and Applications menu.
*   **[detector.py](file:///home/cristina/Documentos/grabarPantalla/detector.py)**: The `ZoomDetector` module using `xwininfo` to inspect active Zoom windows.
*   **[video_recorder.py](file:///home/cristina/Documentos/grabarPantalla/video_recorder.py)**: The `VideoRecorder` module interacting with GNOME Shell's Screencast D-Bus API.
*   **[audio_recorder.py](file:///home/cristina/Documentos/grabarPantalla/audio_recorder.py)**: The `AudioRecorder` module capturing and mixing microphone and/or speakers audio using GStreamer.
*   **[processor.py](file:///home/cristina/Documentos/grabarPantalla/processor.py)**: The `MediaProcessor` module executing FFmpeg for media merging and compression.
*   **[recover.py](file:///home/cristina/Documentos/grabarPantalla/recover.py)**: A recovery script to manually merge and compress leftover temp files if the recorder was interrupted.
*   **[config.py](file:///home/cristina/Documentos/grabarPantalla/config.py)**: The central configuration file managing paths, codecs, qualities, and polling timeouts.
*   **[PROYECTO.md](file:///home/cristina/Documentos/grabarPantalla/PROYECTO.md)**: Technical design and architectural documentation.

---

## 🛠️ Prerequisites and Installation

To allow D-Bus communication with GNOME, audio capture via PipeWire/PulseAudio, and final video compression, system dependencies must be installed on your machine.

### 1. Recommended Installation (System Package Manager)
On Debian, Ubuntu, or Zorin OS distributions, it is highly recommended to install the pre-packaged Python libraries directly using `apt` (this avoids compile steps):

```bash
sudo apt update
sudo apt install python3-dbus python3-gi gstreamer1.0-plugins-good gstreamer1.0-plugins-base gstreamer1.0-plugins-bad ffmpeg x11-utils
```

### 2. Alternative Installation (Pip and requirements.txt)
If you prefer running inside a virtual environment (`venv`) or installing packages via `pip`, use the **[requirements.txt](file:///home/cristina/Documentos/grabarPantalla/requirements.txt)** file.

Because `dbus-python` and `PyGObject` compile native C extensions, you have two options to manage them:

#### Method A: Reusing System Packages (Easiest)
Create a virtual environment that inherits globally installed system packages. This bypasses the need for compiling anything:
1. Install system bindings:
   ```bash
   sudo apt install python3-dbus python3-gi
   ```
2. Create the virtual environment using `--system-site-packages`:
   ```bash
   python3 -m venv --system-site-packages .venv
   ```
3. Activate the environment and run the script.

#### Method B: Installing Build Tools
If you want a fully isolated virtual environment and compile the libraries within it, you must install the build compiler (`gcc`, `make`), Python development headers, and system development packages first:
```bash
sudo apt update
sudo apt install build-essential python3-dev libdbus-1-dev libglib2.0-dev
```
Then run the standard pip command:
```bash
pip install -r requirements.txt
```

---

## 🖥️ Graphical User Interface (GUI) & Desktop Icon

If you prefer a visual window with buttons and a real-time recording timer, you can use the native **GTK 3** GUI.

### 1. Install the Desktop and Menu Shortcuts
We have included an installer script that creates a launcher icon on your Desktop and indexes the application into Zorin OS/GNOME application search.

Run the installer:
```bash
python3 install.py
```

This creates the **Zoom & Screen Recorder** launcher in:
*   Your **Desktop** (`~/Escritorio/grabador-zoom.desktop`).
*   Your **Applications Menu** (system app grid).

### 2. Run the GUI
Double-click the **Zoom & Screen Recorder** desktop icon, search for it in your application grid, or launch it via the terminal:
```bash
python3 gui.py
```

*   **GUI Usage**:
    *   **Select Mode**: Choose "Automatic" to wait for Zoom meetings in the background, or "Manual" to capture full screen immediately.
    *   **Record**: Click the suggested **Record** button (highlights in green/blue) to start. The digital timer will count elapsed time in `HH:MM:SS`.
    *   **Stop**: Click the **Stop** button (red). Recording stops instantly, and compression processes asynchronously in a background thread to prevent UI freezing.

---

## 🚀 Running via Terminal (CLI Mode)

1.  Open terminal and navigate to the project directory:
    ```bash
    cd /home/cristina/Documentos/grabarPantalla
    ```
2.  Start the application:
    ```bash
    python3 main.py
    ```
3.  **Mode Prompts**:
    *   You will be asked to choose between **1** (Automatic Zoom daemon) or **2** (Immediate manual full screen).
4.  **CLI Command Line Flags (Shortcuts)**:
    *   Skip the prompt and start in **Automatic Zoom** daemon mode directly:
        ```bash
        python3 main.py --auto     # or -a
        ```
    *   Skip the prompt and start in **Manual Full Screen** recording immediately:
        ```bash
        python3 main.py --manual   # or -m
        ```
5.  **Graceful Exit**:
    *   Press `Ctrl + C` to stop the script safely. If a recording is actively running, it will automatically save and process the media before exiting to prevent file corruption.

---

## ⚙️ Custom Configurations

All variables are centralized in **[config.py](file:///home/cristina/Documentos/grabarPantalla/config.py)**. You can open and edit it to change paths, qualities, and behaviors:

```python
# Output folder for final MP4 videos
OUTPUT_DIR = "/home/cristina/Documentos/Zoom"

# Frame rate for video files (10 FPS keeps files tiny while maintaining readability)
VIDEO_FRAMERATE = 10

# Constant Rate Factor (CRF: 18-28. Higher means more compression)
VIDEO_CRF = 24

# Set to True if you want to record your own microphone along with speaker audio
RECORD_MICROPHONE = False
```

---

## 📄 License

This project is licensed under the **MIT License**. See the **[LICENSE](file:///home/cristina/Documentos/grabarPantalla/LICENSE)** file for legal terms.
