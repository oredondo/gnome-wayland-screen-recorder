import os
import logging
import subprocess
import glob
from faster_whisper import WhisperModel
import pipeline_config

logger = logging.getLogger(__name__)

class AudioTranscriber:
    """Transcribes audio file to text in memory-efficient chunks using faster-whisper."""

    def __init__(
        self,
        audio_path: str,
        temp_dir: str,
        include_timestamps: bool = True,
        initial_prompt: str = None
    ):
        self.audio_path = audio_path
        self.temp_dir = temp_dir
        self.include_timestamps = include_timestamps
        self.initial_prompt = initial_prompt
        self.output_temp_file = os.path.join(temp_dir, "transcription_temp.txt")

    def transcribe(self) -> str:
        """Splits audio into 30-minute chunks and runs transcription on each to avoid OOM."""
        os.makedirs(self.temp_dir, exist_ok=True)

        if not os.path.exists(self.audio_path) or os.path.getsize(self.audio_path) == 0:
            raise ValueError("El archivo de audio no existe o está vacío.")

        import time
        normalized_wav = os.path.join(self.temp_dir, f"norm_{int(time.time() * 1000)}.wav")
        logger.info(f"Normalizing audio {self.audio_path} to 16kHz mono PCM WAV...")

        cmd_norm = [
            "ffmpeg", "-y", "-i", self.audio_path,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ac", "1", "-ar", "16000", "-codec:a", "pcm_s16le",
            normalized_wav
        ]
        try:
            subprocess.run(cmd_norm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            audio_source_path = normalized_wav
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode('utf-8', errors='ignore')
            logger.error(f"FFmpeg audio normalization failed: {err_msg}")
            raise ValueError("El archivo de audio no contiene datos válidos o está dañado.")

        try:
            logger.info(f"Splitting normalized audio into 30-minute chunks...")
            chunk_pattern = os.path.join(self.temp_dir, "audio_chunk_%03d.wav")

            cmd = [
                "ffmpeg", "-y", "-i", audio_source_path,
                "-f", "segment", "-segment_time", "1800",
                "-c", "copy", chunk_pattern
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            chunk_files = sorted(glob.glob(os.path.join(self.temp_dir, "audio_chunk_*.wav")))
            if not chunk_files:
                chunk_files = [audio_source_path]
        except Exception as e:
            logger.warning(f"Segment splitting fallback to single file: {e}")
            chunk_files = [audio_source_path]

        logger.info(f"Audio split successfully into {len(chunk_files)} chunks.")

        whisper_model = getattr(pipeline_config, "WHISPER_MODEL", "base")
        logger.info(f"Loading Whisper model '{whisper_model}' on CPU (int8 quantization)...")
        model = WhisperModel(whisper_model, device="cpu", compute_type="int8")

        transcribed_segments = []

        # Process each chunk sequentially to keep memory usage low
        for idx, chunk_file in enumerate(chunk_files):
            offset_sec = idx * 1800
            logger.info(f"Transcribing audio chunk {idx+1}/{len(chunk_files)}: {os.path.basename(chunk_file)} (Offset: {offset_sec}s)...")

            segments, info = model.transcribe(
                chunk_file,
                beam_size=5,
                language="es",
                initial_prompt=self.initial_prompt,
                vad_filter=True
            )

            if idx == 0:
                logger.info(f"Detected language: {info.language} with probability {info.language_probability:.2f}")

            for segment in segments:
                text_clean = segment.text.strip()
                if not text_clean:
                    continue
                if self.include_timestamps:
                    current_sec = int(segment.start) + offset_sec
                    minutes, seconds = divmod(current_sec, 60)
                    timestamp_str = f"[{minutes:02d}:{seconds:02d}]"
                    line = f"{timestamp_str} {text_clean}\n"
                else:
                    line = f"{text_clean}\n"
                transcribed_segments.append(line)
                
            # Clean up this chunk file immediately to save disk space
            try:
                os.remove(chunk_file)
            except Exception as e:
                logger.warning(f"Failed to remove temporary chunk file {chunk_file}: {e}")
                
        # Write unified transcription to temp file
        full_text = "".join(transcribed_segments)
        with open(self.output_temp_file, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        if os.path.exists(normalized_wav):
            try:
                os.remove(normalized_wav)
            except OSError:
                pass

        logger.info(f"Audio transcription finished. Saved to {self.output_temp_file}")
        return self.output_temp_file
