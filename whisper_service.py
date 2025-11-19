"""
Whisper Service - Optimized transcription pipeline
GPU support, anti-bot protection, guaranteed cleanup
"""

import os
from typing import List, Dict
import yt_dlp
import whisper


class WhisperService:
    """Handles YouTube audio transcription using OpenAI Whisper"""

    def __init__(self, model_size: str = "base", device: str = None):
        """
        Initialize Whisper service.

        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large').
            device: Force 'cpu' or 'cuda'. Auto-detect if None.
        """
        print(f"🎤 Loading Whisper model: {model_size}...")

        try:
            import torch
            device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        except ImportError:
            device = "cpu"
        
        self.model = whisper.load_model(model_size, device=device)

        print(f"✓ Whisper model ready (device = {device})")

    # ----------------------------------------------------------------------

    @staticmethod
    def _get_temp_audio_filename(video_id: str) -> str:
        """Generate a clean temporary filename for the mp3 audio."""
        return f"temp_audio_{video_id}.mp3"

    # ----------------------------------------------------------------------

    @staticmethod
    def download_audio(video_id: str) -> str:
        """
        Download YouTube video audio directly as MP3.
        Includes anti-bot protection.

        Returns:
            Path to downloaded MP3 file.
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        audio_path = WhisperService._get_temp_audio_filename(video_id)

        print("📥 Downloading audio...")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"temp_audio_{video_id}.%(ext)s",  # Let yt-dlp set extension
            "quiet": True,
            "no_warnings": True,

            # Convert to mp3 directly
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],

            # Retry + stability
            "retries": 3,
            "noplaylist": True,
            "keepvideo": False,  # Delete original video file after conversion

            # Anti-bot detection bypass
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                    "skip": ["dash", "hls"]
                }
            },
            "http_headers": {
                "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-us,en;q=0.5",
                "Sec-Fetch-Mode": "navigate",
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Check if file exists (yt-dlp sometimes creates different extensions)
            if not os.path.exists(audio_path):
                # Check for alternative extensions
                base_name = f"temp_audio_{video_id}"
                for ext in [".m4a", ".webm", ".opus", ".mp3"]:
                    alt_file = base_name + ext
                    if os.path.exists(alt_file):
                        # Rename to .mp3
                        os.rename(alt_file, audio_path)
                        print(f"✓ Audio downloaded and converted: {audio_path}")
                        return audio_path
                
                # If still not found, list what files exist for debugging
                import glob
                existing_files = glob.glob(f"{base_name}*")
                error_msg = f"yt-dlp did not create: {audio_path}"
                if existing_files:
                    error_msg += f"\nFound these files instead: {existing_files}"
                raise FileNotFoundError(error_msg)

            print(f"✓ Audio downloaded: {audio_path}")
            return audio_path

        except Exception as e:
            raise Exception(f"Failed to download audio: {e}")

    # ----------------------------------------------------------------------

    def transcribe_audio(self, audio_path: str) -> List[Dict]:
        """
        Transcribe an audio file using Whisper.
        Ensures cleanup regardless of success/failure.
        """
        print("🎤 Transcribing audio with Whisper...")
        print("   (This may take 1–3 minutes depending on video length)")

        try:
            result = self.model.transcribe(audio_path, verbose=False)

            transcript = [
                {
                    "text": segment["text"].strip(),
                    "start": segment["start"],
                    "duration": segment["end"] - segment["start"],
                }
                for segment in result["segments"]
            ]

            print(f"✓ Transcription complete: {len(transcript)} segments")
            return transcript

        except Exception as e:
            raise Exception(f"Transcription failed: {e}")

        finally:
            # ALWAYS clean up temporary file (even on error)
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print("✓ Temporary audio file removed")

    # ----------------------------------------------------------------------

    def transcribe_video(self, video_id: str) -> List[Dict]:
        """Full pipeline: download audio → transcribe → cleanup."""
        audio_path = self.download_audio(video_id)
        return self.transcribe_audio(audio_path)