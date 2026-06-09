import os
import glob
import subprocess
import shutil
import sys
from datetime import datetime

import config
from processor import MediaProcessor

def recover_latest_recording():
    print("=========================================================")
    print("       Recuperador de Grabaciones Temporales             ")
    print("=========================================================")
    
    processor = MediaProcessor()
    if not processor.is_available():
        print("[ERROR] FFmpeg no está instalado en este sistema.")
        print("        Por favor instálalo ejecutando: sudo apt update && sudo apt install ffmpeg")
        return
        
    # Search for temp videos
    # GNOME screencast saves to the user's Videos folder
    videos_dir_es = os.path.expanduser("~/Vídeos")
    videos_dir_en = os.path.expanduser("~/Videos")
    
    video_patterns = [
        os.path.join(videos_dir_es, "temp_zoom_video_*.webm"),
        os.path.join(videos_dir_en, "temp_zoom_video_*.webm"),
        os.path.join(config.TEMP_DIR, "temp_zoom_video_*.webm"),
        "temp_zoom_video_*.webm"
    ]
    
    video_files = []
    for pattern in video_patterns:
        video_files.extend(glob.glob(pattern))
        
    # Search for temp audios
    audio_files = glob.glob(os.path.join(config.TEMP_DIR, "temp_zoom_audio_*.ogg"))
    
    if not video_files:
        print("[INFO] No se encontraron archivos de vídeo temporal 'temp_zoom_video_*.webm'.")
        return
    if not audio_files:
        print("[INFO] No se encontraron archivos de audio temporal 'temp_zoom_audio_*.ogg'.")
        return
        
    # Sort by modification time (most recent first)
    video_files.sort(key=os.path.getmtime, reverse=True)
    audio_files.sort(key=os.path.getmtime, reverse=True)
    
    latest_video = video_files[0]
    latest_audio = audio_files[0]
    
    print(f"\nSe han detectado las siguientes grabaciones más recientes:")
    print(f"  Vídeo: {os.path.basename(latest_video)} ({datetime.fromtimestamp(os.path.getmtime(latest_video)).strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"  Audio: {os.path.basename(latest_audio)} ({datetime.fromtimestamp(os.path.getmtime(latest_audio)).strftime('%Y-%m-%d %H:%M:%S')})")
    
    confirm = input("\n¿Deseas fusionar y comprimir estos archivos ahora? (S/n): ").strip().lower()
    if confirm not in ("", "s", "si", "yes"):
        print("Operación cancelada.")
        return
        
    # Generate final file name based on video file modification time or current time
    mtime = os.path.getmtime(latest_video)
    dt = datetime.fromtimestamp(mtime)
    filename = f"{dt.strftime(config.FILENAME_FORMAT)}.mp4"
    output_path = os.path.join(config.OUTPUT_DIR, filename)
    
    print(f"\n[INFO] Procesando y comprimiendo grabación a: {output_path}")
    success = processor.merge_and_compress(latest_video, latest_audio, output_path)
    if success:
        print(f"[ÉXITO] Grabación recuperada y guardada como: {filename}\n")
    else:
        print("[ERROR] Falló la compresión con FFmpeg. Asegúrate de que no haya problemas con los archivos temporales.\n")

if __name__ == "__main__":
    recover_latest_recording()
