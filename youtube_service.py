"""
YouTube service - handles video data extraction
"""

import re
import yt_dlp
from typing import Dict, List
from youtube_transcript_api import YouTubeTranscriptApi
from models import VideoMetadata


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
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
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
            # Create instance and call list with video_id
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            
            # Try to get English transcript
            try:
                transcript = transcript_list.find_transcript(['en'])
                data = transcript.fetch()
            except:
                # Try auto-generated English
                try:
                    transcript = transcript_list.find_transcript(['en-US'])
                    data = transcript.fetch()
                except:
                    # Get first available transcript
                    for transcript in transcript_list:
                        data = transcript.fetch()
                        break
            
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