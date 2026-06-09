import os

# ==============================================================================
#                      GENERAL RECORDER CONFIGURATIONS
# ==============================================================================

# Application Directories
OUTPUT_DIR = "/home/cristina/Documentos/Zoom"
TEMP_DIR = "/home/cristina/Documentos/grabarPantalla/.temp"
LOG_FILE = os.path.join(OUTPUT_DIR, "zoom_recorder.log")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Final file name timestamp format (e.g., 20260609_2225)
# Reference: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
FILENAME_FORMAT = "%Y%m%d_%H%M"

# Polling interval in seconds to check for active Zoom meetings
POLLING_INTERVAL = 3

# ==============================================================================
#                  SCREEN AND AUDIO CAPTURE CONFIGURATIONS
# ==============================================================================

# Capture and show mouse cursor in the recording
DRAW_CURSOR = True

# Record laptop microphone input
# If False, only the system internal audio (other meeting participants) will be recorded
RECORD_MICROPHONE = False

# Window names to ignore during Zoom active call detection
# (Prevents capturing secondary control bars, clipboards, or empty main windows)
ZOOM_IGNORED_TITLES = {
    "zoom workplace", 
    "zoom", 
    "qt selection owner for zoom",
    "chromium clipboard"
}

# ==============================================================================
#                  FFMPEG COMPRESSION AND ENCODING SETTINGS
# ==============================================================================

# Output video frame rate (FPS)
# Note: 10 FPS drastically reduces file size and is perfect for slides/text sharing
VIDEO_FRAMERATE = 10

# Constant Rate Factor (CRF) quality control
# Recommended range: 18 (highest quality, larger files) to 28 (lower quality, smaller files)
VIDEO_CRF = 24

# Video codec to use
VIDEO_CODEC = "libx264"

# Encoding speed preset
# Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
# 'slow' optimizes output file size to the maximum for the selected quality
VIDEO_PRESET = "slow"

# Encoder tune profile
# 'stillimage' optimizes H.264 compression for slides, static text, and desktop layouts
VIDEO_TUNE = "stillimage"

# Pixel format for the final output
# 'yuv420p' ensures maximum compatibility with web browsers and mobile media players
VIDEO_PIX_FMT = "yuv420p"

# Audio codec to use for the final merge
AUDIO_CODEC = "aac"

# Audio bitrate
# 96k provides clean voice quality while using minimal disk space
AUDIO_BITRATE = "96k"
