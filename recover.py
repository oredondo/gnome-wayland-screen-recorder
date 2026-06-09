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
    print("           Temporary Recordings Recovery Tool            ")
    print("=========================================================")
    
    processor = MediaProcessor()
    if not processor.is_available():
        print("[ERROR] FFmpeg is not installed on this system.")
        print("        Please install it by running: sudo apt update && sudo apt install ffmpeg")
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
        print("[INFO] No temporary video files 'temp_zoom_video_*.webm' were found.")
        return
    if not audio_files:
        print("[INFO] No temporary audio files 'temp_zoom_audio_*.ogg' were found.")
        return
        
    # Sort by modification time (most recent first)
    video_files.sort(key=os.path.getmtime, reverse=True)
    audio_files.sort(key=os.path.getmtime, reverse=True)
    
    latest_video = video_files[0]
    latest_audio = audio_files[0]
    
    print(f"\nThe following recent temporary recordings have been detected:")
    print(f"  Video: {os.path.basename(latest_video)} ({datetime.fromtimestamp(os.path.getmtime(latest_video)).strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"  Audio: {os.path.basename(latest_audio)} ({datetime.fromtimestamp(os.path.getmtime(latest_audio)).strftime('%Y-%m-%d %H:%M:%S')})")
    
    confirm = input("\nDo you wish to merge and compress these files now? (Y/n): ").strip().lower()
    if confirm not in ("", "y", "yes", "s", "si"):
        print("Operation canceled.")
        return
        
    # Generate final file name based on video file modification time or current time
    mtime = os.path.getmtime(latest_video)
    dt = datetime.fromtimestamp(mtime)
    filename = f"{dt.strftime(config.FILENAME_FORMAT)}.mp4"
    output_path = os.path.join(config.OUTPUT_DIR, filename)
    
    print(f"\n[INFO] Merging and compressing recording to: {output_path}")
    success = processor.merge_and_compress(latest_video, latest_audio, output_path)
    if success:
        print(f"[SUCCESS] Recording recovered and saved as: {filename}\n")
    else:
        print("[ERROR] FFmpeg compression failed. Check the temporary files for errors.\n")

if __name__ == "__main__":
    recover_latest_recording()
