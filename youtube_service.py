"""YouTube service - handles video data extraction."""

import os
import re
from typing import Dict, List, Tuple

import yt_dlp
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    TooManyRequests,
)
from models import VideoMetadata
from config import Config


class YouTubeService:
    """Handles YouTube video data extraction"""
    
    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]*)',
            r'youtube\.com\/embed\/([^&\n?]*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Invalid YouTube URL")
    
    @staticmethod
    def get_video_metadata(url: str) -> VideoMetadata:
        """Get video metadata using yt-dlp (reliable method)"""
        try:
            print("📊 Fetching video metadata...")
            
            cookie_file, _ = YouTubeService._get_cookie_settings()
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                # Anti-bot detection bypass options
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['dash', 'hls']
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                }
            }
            if cookie_file:
                ydl_opts['cookiefile'] = cookie_file
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                duration_seconds = info.get('duration', 0)
                duration_minutes = duration_seconds // 60 if duration_seconds else 0
                
                return VideoMetadata(
                    title=info.get('title', 'Unknown'),
                    duration=f"{duration_minutes} minutes" if duration_minutes else "Unknown",
                    author=info.get('uploader', 'Unknown'),
                    views=f"{info.get('view_count', 0):,}" if info.get('view_count') else "Unknown"
                )
        except Exception as e:
            print(f"[DEBUG] Metadata fetch failed: {e}")
            # Fallback
            video_id = YouTubeService.extract_video_id(url)
            return VideoMetadata(
                title=f"YouTube Video ({video_id})",
                duration="Unknown",
                author="Unknown",
                views="Unknown"
            )
    
    @staticmethod
    def get_transcript(video_id: str) -> List[Dict]:
        """Fetch video transcript"""
        try:
            # Fetch available transcripts for the video
            _, cookies = YouTubeService._get_cookie_settings()
            
            # Add custom headers to bypass bot detection
            transcript_list = YouTubeTranscriptApi.list_transcripts(
                video_id,
                cookies=cookies,
            )
            
            # Try to get English transcript
            try:
                transcript = transcript_list.find_transcript(['en'])
                data = transcript.fetch()
            except Exception:
                # Try auto-generated English
                try:
                    transcript = transcript_list.find_transcript(['en-US'])
                    data = transcript.fetch()
                except Exception:
                    # Fallback: use the first available transcript
                    first_available = next(iter(transcript_list), None)
                    if not first_available:
                        raise Exception("No transcripts available for this video")
                    data = first_available.fetch()
            
            # Convert FetchedTranscriptSnippet objects to dictionaries
            return [
                {
                    'text': entry.text,
                    'start': entry.start,
                    'duration': entry.duration
                }
                for entry in data
            ]
                    
        except Exception as e:
            raise Exception(f"Could not fetch transcript: {str(e)}. Video may not have captions.")
    
    @staticmethod
    def format_transcript(transcript: List[Dict]) -> str:
        """Format transcript with timestamps"""
        formatted = []
        for entry in transcript:
            time = YouTubeService._format_timestamp(entry['start'])
            text = entry['text']
            formatted.append(f"[{time}] {text}")
        return "\n".join(formatted)
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    @staticmethod
    def _get_cookie_settings() -> Tuple[str | None, Dict[str, str] | None]:
        """Resolve cookie file path and dictionary for authenticated requests."""
        cookie_path = Config.YOUTUBE_COOKIES_FILE
        if not cookie_path:
            return None, None

        expanded_path = os.path.abspath(os.path.expanduser(cookie_path))
        if not os.path.exists(expanded_path):
            if Config.DEBUG_MODE:
                print(f"[DEBUG] Cookie file not found at {expanded_path}; continuing without cookies")
            return None, None

        cookies: Dict[str, str] = {}
        try:
            with open(expanded_path, "r", encoding="utf-8") as cookie_file:
                for line in cookie_file:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 7:
                        continue
                    name, value = parts[5], parts[6]
                    cookies[name] = value
        except Exception as err:
            if Config.DEBUG_MODE:
                print(f"[DEBUG] Failed to load cookies: {err}; continuing without cookies")
            return None, None

        if Config.DEBUG_MODE:
            print(f"[DEBUG] Loaded cookies from {expanded_path}")
        return expanded_path, cookies