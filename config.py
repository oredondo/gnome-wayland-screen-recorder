import os

# ==============================================================================
#                      CONFIGURACIÓN GENERAL DEL GRABADOR
# ==============================================================================

# Directorios de la aplicación
OUTPUT_DIR = "/home/cristina/Vídeos/"
TEMP_DIR = "/home/cristina/Documentos/grabarPantalla/.temp"
LOG_FILE = os.path.join(OUTPUT_DIR, "zoom_recorder.log")

# Asegurar que los directorios existan
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Formato del nombre de archivo final (ej. 20260609_2225)
# Referencia: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
FILENAME_FORMAT = "%Y%m%d_%H%M"

# Intervalo en segundos para comprobar si hay reuniones de Zoom activas
POLLING_INTERVAL = 3

# ==============================================================================
#                  PARÁMETROS DE CAPTURA DE PANTALLA Y AUDIO
# ==============================================================================

# Capturar y mostrar el cursor del ratón en la grabación
DRAW_CURSOR = True

# Grabar la entrada de tu propio micrófono
# Si es False, solo se grabará el sonido interno de la llamada (el audio de los demás participantes)
RECORD_MICROPHONE = False


# Nombres de ventana a ignorar durante la detección de Zoom
# (Evita capturar paneles de control, portapapeles o el chat principal vacío)
ZOOM_IGNORED_TITLES = {
    "zoom workplace", 
    "zoom", 
    "qt selection owner for zoom",
    "chromium clipboard"
}

# ==============================================================================
#                  PARÁMETROS DE COMPRESIÓN Y CODIFICACIÓN (FFMPEG)
# ==============================================================================

# Tasa de fotogramas del vídeo final (FPS)
# Nota: 10 FPS reduce masivamente el tamaño del archivo y es perfecto para diapositivas
VIDEO_FRAMERATE = 10

# Factor de calidad constante (CRF: Constant Rate Factor)
# Rango recomendado: 18 (calidad alta, archivos grandes) a 28 (calidad baja, archivos pequeños)
VIDEO_CRF = 24

# Códec de vídeo a utilizar
VIDEO_CODEC = "libx264"

# Velocidad de compresión (preset)
# Opciones: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
# 'slow' optimiza al máximo el peso del archivo final para la calidad elegida
VIDEO_PRESET = "slow"

# Afinación especial del codificador para el tipo de contenido
# 'stillimage' optimiza H.264 para diapositivas, textos fijos y capturas de escritorio
VIDEO_TUNE = "stillimage"

# Formato de píxeles para el vídeo final
# 'yuv420p' garantiza la máxima compatibilidad con reproductores web y móviles
VIDEO_PIX_FMT = "yuv420p"

# Códec de audio a utilizar para la mezcla final
AUDIO_CODEC = "aac"

# Tasa de bits del audio (bitrate)
# 96k es ideal para voz humana clara y consume un espacio ínfimo
AUDIO_BITRATE = "96k"
