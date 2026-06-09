# Project Definition: Zoom Auto-Recorder

This document outlines the requirements, design specifications, and engineering decisions adopted for the development of the automated Zoom and screen recording application on Linux.

---

## 🎯 Project Goal
Build a hybrid recording utility that runs on Linux desktop environments (GNOME with Wayland or X11) such as Zorin OS or Ubuntu. It offers two user-selectable operating modes:

1.  **Automatic Daemon Mode (Zoom)**: Silently polls system windows in the background. When it detects an active Zoom meeting window, it automatically initiates a full-screen recording. It mixes speaker audio, saves the files, and compiles/compresses them once the meeting window closes.
2.  **Manual Recording Mode**: Immediately records full-screen video and system audio, running indefinitely until the user manually triggers a stop.

In both modes, the application applies highly optimized compression parameters to ensure text, presentations, and screen-sharing contents remain perfectly readable while minimizing file sizes.

---

## 📑 Business and Technical Requirements

### 1. Life Cycle Automation and Control
*   **Automatic Start**: Trigger recording immediately when a Zoom call starts.
*   **Automatic Stop**: Stop and finalize recordings when the Zoom call ends.
*   **Graceful Interrupts**: If the application receives termination signals (`Ctrl + C` / `SIGINT` / `SIGTERM`), it must stop recording and force-process all cached data to prevent file corruption.

### 2. Output File Naming Convention
*   The final filename must represent the local date and time of the save: `YYYYMMDD_HHMM.mp4` (e.g., `20260609_2220.mp4`).

### 3. High Quality and High Compression
*   **Readability**: Compressions must keep texts, slide details, and code sharing sharp.
*   **Low Footprint**: Video encoding bitrates must decrease when the screen is static, saving disk space.

### 4. Structural Design (OOP)
*   Object-Oriented Programming (OOP) architecture.
*   Modular files under 150 lines for clean code and high maintainability.

---

## 🏗️ Architectural and Engineering Decisions

To handle Wayland's security isolation policies (which block standard X11 capturing tools), we chose the following architecture:

```mermaid
graph TD
    A1[main.py: ZoomRecorderApp] --> B[detector.py: ZoomDetector]
    A1 --> C[video_recorder.py: VideoRecorder]
    A1 --> D[audio_recorder.py: AudioRecorder]
    A1 --> E[processor.py: MediaProcessor]
    
    A2[gui.py: ZoomRecorderGUI] --> B
    A2 --> C
    A2 --> D
    A2 --> E
    
    C -->|D-Bus| F[GNOME Shell Screencast API]
    D -->|GStreamer| G[PipeWire / PulseAudio Mixer]
    E -->|Subprocess| H[FFmpeg Encoder]
    
    F -->|Creates| I[video_temp.webm]
    G -->|Creates| J[audio_temp.ogg]
    H -->|Merges & Compresses CRF+10FPS| K[Timestamp.mp4]
```

### Wayland Desktop Capture
*   **Decision**: GNOME Shell Screencast D-Bus API (`org.gnome.Shell.Screencast`).
*   **Why**: Traditional screen grabbers like `ffmpeg -f x11grab` result in black screens on Wayland. Standards like the XDG Desktop Portal trigger popups for permission on every launch. GNOME's native Screencast API allows silent, high-performance capture directly from the compositor buffers.

### Dynamic Audio Capture and Mixing
*   **Decision**: GStreamer pipeline with `pulsesrc` and optional `audiomixer` configured dynamically via `GstDeviceMonitor`.
*   **Why**: Zoom meetings require capturing system audio output (other participants). Capturing only the microphone misses the conversation. We scan for the active speaker output and microphone, mix them if enabled (`RECORD_MICROPHONE` in config), and save directly into an Opus compressed Ogg container to save CPU.

### Compression Profile Tuning
To compress static desktop slide-sharing meetings with high efficiency, we configured the following FFmpeg command parameters:

| Parameter | Value | Technical Justification |
| :--- | :--- | :--- |
| **Output FPS** | `10 fps` | Dropping framerates from 30 to 10 FPS cuts out redundant frames. For slide sharing, this saves up to 70% disk space with zero loss in readability. |
| **Video Codec** | `libx264` | Offers universal compatibility across web browsers, smartphones, and players. |
| **Quality (CRF)** | `24` | Constant Rate Factor 24 adjusts bitrates dynamically. It stays near zero for static slides, allocating bits only when movement occurs. |
| **Encoding Tune** | `stillimage` | Optimizes H.264 compression specifically for slide decks and flat text, reducing fuzzy compression artifacts around characters. |
| **Encoding Preset**| `slow` | Instructs the encoder to analyze frames more thoroughly, compressing files further. |
| **Audio Codec** | `AAC at 96k` | Perfect quality for speech while maintaining a negligible file size. |
