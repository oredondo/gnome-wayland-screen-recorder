import subprocess
import shutil
import os
import logging
import config

logger = logging.getLogger(__name__)

class MediaProcessor:
    """Merges and compresses the video and audio files using FFmpeg."""
    
    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg")
        
    def is_available(self) -> bool:
        """Returns True if ffmpeg is installed, False otherwise."""
        return self.ffmpeg_path is not None

    def merge_and_compress(self, video_path: str, audio_path: str, output_path: str) -> bool:
        """Merges and compresses the video and audio files into the output MP4 file."""
        if not self.is_available():
            logger.error("FFmpeg is not installed on this system. Cannot merge and compress files.")
            print("\n[ERROR] FFmpeg no está instalado. Por favor instálalo ejecutando:")
            print("        sudo apt update && sudo apt install ffmpeg\n")
            return False
            
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return False
            
        # Ensure the output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
            
        # FFmpeg command for high compression screen recording, reading from config.py:
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter:v", f"fps=fps={config.VIDEO_FRAMERATE}",
            "-c:v", config.VIDEO_CODEC,
            "-crf", str(config.VIDEO_CRF),
            "-preset", config.VIDEO_PRESET,
            "-tune", config.VIDEO_TUNE,
            "-c:a", config.AUDIO_CODEC,
            "-b:a", config.AUDIO_BITRATE,
            "-pix_fmt", config.VIDEO_PIX_FMT,
            output_path
        ]

        
        logger.info(f"Running FFmpeg merge command: {' '.join(cmd)}")
        try:
            # Run FFmpeg and capture outputs in case of error
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info(f"FFmpeg command completed successfully. Saved to {output_path}")
            
            # Clean up temporary files upon success
            try:
                os.remove(video_path)
                os.remove(audio_path)
                logger.info("Temporary recording files removed.")
            except Exception as cleanup_err:
                logger.warning(f"Failed to remove temporary files: {cleanup_err}")
                
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed with exit code {e.returncode}")
            logger.error(f"FFmpeg stderr: {e.stderr.decode('utf-8')}")
            return False
        except Exception as e:
            logger.error(f"Error executing FFmpeg: {e}")
            return False
