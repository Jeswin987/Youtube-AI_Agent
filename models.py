"""
Data models for YouTube Agent
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VideoMetadata:
    """Video metadata from YouTube"""
    title: str
    duration: str
    author: str
    views: str


@dataclass
class VideoAnalysis:
    """Complete video analysis results"""
    title: str
    duration: str
    summary: str
    key_timestamps: List[Dict[str, str]]
    themes: List[str]
    content_breakdown: Dict[str, str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export"""
        return {
            'title': self.title,
            'duration': self.duration,
            'summary': self.summary,
            'key_timestamps': self.key_timestamps,
            'themes': self.themes,
            'content_breakdown': self.content_breakdown
        }

