"""
Whisper Service - Transcribes videos without captions
Makes agent work on ANY video (truly autonomous)
"""

import whisper
import yt_dlp
import os
from typing import List, Dict


class WhisperService:
    """Handles audio transcription using OpenAI Whisper"""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper service
        
        Args:
            model_size: 'tiny', 'base', 'small', 'medium', 'large'
                       'base' is recommended (good speed/accuracy balance)
        """
        print(f"🎤 Loading Whisper '{model_size}' model (first time: ~150MB download)...")
        self.model = whisper.load_model(model_size)
        print("✓ Whisper model ready")
    
    @staticmethod
    def download_audio(video_id: str) -> str:
        """Download audio from YouTube video"""
        url = f"https://www.youtube.com/watch?v={video_id}"
        audio_file = f'temp_audio_{video_id}.mp3'
        
        print("📥 Downloading audio from video...")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': audio_file.replace('.mp3', '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("✓ Audio downloaded")
            return audio_file
        except Exception as e:
            raise Exception(f"Failed to download audio: {str(e)}")
    
    def transcribe_audio(self, audio_path: str) -> List[Dict]:
        """
        Transcribe audio file using Whisper
        
        Returns:
            List of transcript entries with text, start time, and duration
        """
        print("🎤 Transcribing audio with Whisper AI...")
        print("    (This takes 1-3 minutes depending on video length)")
        
        try:
            # Transcribe with timestamps
            result = self.model.transcribe(
                audio_path,
                verbose=False
            )
            
            # Format like YouTube transcript
            transcript = []
            for segment in result['segments']:
                transcript.append({
                    'text': segment['text'].strip(),
                    'start': segment['start'],
                    'duration': segment['end'] - segment['start']
                })
            
            print(f"✓ Transcription complete: {len(transcript)} segments")
            
            # Clean up audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print("✓ Temporary audio file cleaned up")
            
            return transcript
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(audio_path):
                os.remove(audio_path)
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe_video(self, video_id: str) -> List[Dict]:
        """
        Complete workflow: Download audio and transcribe
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Transcript entries
        """
        audio_path = self.download_audio(video_id)
        transcript = self.transcribe_audio(audio_path)
        return transcript