"""
Main YouTube Agent - Enhanced with Whisper autonomous fallback
"""

from youtube_service import YouTubeService
from llm_provider import LLMProvider
from analyzer import VideoAnalyzer
from whisper_service import WhisperService
from models import VideoAnalysis
from config import Config


class YouTubeAgent:
    """Main agent that orchestrates video analysis with autonomous capabilities"""
    
    def __init__(self, llm_provider: str = None, api_key: str = None, use_whisper: bool = True):
        """
        Initialize YouTube Agent
        
        Args:
            llm_provider: 'groq', 'ollama', or 'google' (optional, uses config default)
            api_key: API key for Groq or Google (optional, uses config default)
            use_whisper: Enable Whisper for videos without captions (default: True)
        """
        self.youtube_service = YouTubeService()
        self.llm = LLMProvider(llm_provider, api_key)
        self.analyzer = VideoAnalyzer(self.llm)
        
        # Initialize Whisper if enabled
        self.use_whisper = use_whisper
        self.whisper_service = None
        
        if use_whisper:
            try:
                print("\n🤖 Initializing Whisper AI (autonomous fallback system)...")
                self.whisper_service = WhisperService(model_size="base")
                print("✓ Agent can now handle videos without captions!\n")
            except Exception as e:
                print(f"⚠️  Whisper initialization failed: {e}")
                print("⚠️  Agent will only work with videos that have captions\n")
                self.whisper_service = None
    
    def _calculate_video_duration(self, transcript: list) -> float:
        """
        Calculate video duration in minutes from transcript
        
        Args:
            transcript: List of transcript entries
            
        Returns:
            Duration in minutes
        """
        if not transcript:
            return 0
        
        last_entry = transcript[-1]
        duration_seconds = last_entry['start'] + last_entry.get('duration', 0)
        return duration_seconds / 60
    
    def _get_word_count_for_duration(self, duration_minutes: float) -> str:
        """
        Get appropriate word count based on video duration
        Uses dynamic rules from config or returns default
        
        Args:
            duration_minutes: Video duration in minutes
            
        Returns:
            Word count range as string (e.g., "200-300")
        """
        # Check if dynamic word count is enabled
        if not Config.ENABLE_DYNAMIC_WORD_COUNT:
            if Config.DEBUG_MODE:
                print(f"[DEBUG] Dynamic word count disabled, using default: {Config.SUMMARY_WORD_COUNT}")
            return Config.SUMMARY_WORD_COUNT
        
        # Use dynamic rules from config
        for max_duration, word_count in sorted(Config.DYNAMIC_WORD_COUNT_RULES.items()):
            if duration_minutes < max_duration:
                if Config.DEBUG_MODE:
                    print(f"[DEBUG] Video {duration_minutes:.1f} min < {max_duration} min → {word_count} words")
                return word_count
        
        # Fallback to default
        if Config.DEBUG_MODE:
            print(f"[DEBUG] No matching rule, using default: {Config.SUMMARY_WORD_COUNT}")
        return Config.SUMMARY_WORD_COUNT
    
    def _get_transcript_intelligently(self, video_id: str) -> list[dict]:
        """
        AGENTIC BEHAVIOR: Try captions first, auto-fallback to Whisper
        This demonstrates autonomous decision-making
        """
        # Attempt 1: YouTube Captions (faster)
        try:
            print("📝 Attempting to fetch YouTube captions...")
            transcript = self.youtube_service.get_transcript(video_id)
            print("✓ Captions found! Using YouTube captions.\n")
            return transcript
            
        except Exception as caption_error:
            # AGENT DECISION POINT: No captions available
            print("⚠️  No captions available for this video")
            
            if self.whisper_service:
                print("\n" + "="*80)
                print("🤖 AGENT AUTONOMOUS DECISION:")
                print("   Captions failed → Switching to Whisper AI transcription")
                print("   (This demonstrates true agentic behavior!)")
                print("="*80 + "\n")
                
                # Attempt 2: Whisper Transcription
                try:
                    transcript = self.whisper_service.transcribe_video(video_id)
                    print("\n✓ Whisper transcription successful!")
                    print("✓ Agent successfully recovered from caption failure\n")
                    return transcript
                except Exception as whisper_error:
                    raise Exception(
                        f"Both caption and Whisper transcription failed.\n"
                        f"Caption error: {caption_error}\n"
                        f"Whisper error: {whisper_error}"
                    )
            else:
                raise Exception(
                    f"Video has no captions and Whisper is not available.\n"
                    f"Error: {caption_error}"
                )
    
    def analyze_video(self, youtube_url: str) -> VideoAnalysis:
        """
        Analyze a YouTube video with autonomous transcript fetching
        
        Args:
            youtube_url: Full YouTube URL
            
        Returns:
            VideoAnalysis object with complete analysis
        """
        print("🎬 Starting video analysis...")
        
        # Extract video ID
        video_id = self.youtube_service.extract_video_id(youtube_url)
        print(f"✓ Video ID extracted: {video_id}")
        
        # Get metadata
        metadata = self.youtube_service.get_video_metadata(youtube_url)
        print(f"✓ Metadata retrieved: {metadata.title}")
        
        # Get transcript (with intelligent fallback)
        print("")
        transcript = self._get_transcript_intelligently(video_id)
        transcript_text = self.youtube_service.format_transcript(transcript)
        print(f"✓ Transcript obtained: {len(transcript)} entries\n")
        
        # Calculate video duration and determine appropriate word count
        video_duration = self._calculate_video_duration(transcript)
        word_count = self._get_word_count_for_duration(video_duration)
        
        print(f"📏 Video duration: {video_duration:.1f} minutes")
        print(f"📝 Target summary length: {word_count} words")
        
        # Generate analysis
        print("\n🤖 Generating AI analysis...")
        
        print("  → Creating summary...")
        summary = self.analyzer.generate_summary(transcript_text, word_count)
        
        print("  → Extracting key timestamps...")
        timestamps = self.analyzer.extract_timestamps_simple(transcript_text)
        
        print("  → Identifying themes...")
        themes = self.analyzer.identify_themes(transcript_text)
        
        print("  → Creating content breakdown...")
        breakdown = self.analyzer.create_content_breakdown(transcript_text)
        
        print("\n✅ Analysis complete!\n")
        
        # Use calculated duration if metadata failed
        duration_str = metadata.duration
        if duration_str == "Unknown" and video_duration > 0:
            duration_str = f"{video_duration:.1f} minutes"
        
        return VideoAnalysis(
            title=metadata.title,
            duration=duration_str,
            summary=summary,
            key_timestamps=timestamps,
            themes=themes,
            content_breakdown=breakdown
        )
    
    def print_analysis(self, analysis: VideoAnalysis):
        """Pretty print the analysis"""
        print("=" * 80)
        print(f"📺 VIDEO ANALYSIS: {analysis.title}")
        print("=" * 80)
        print(f"\n⏱️  Duration: {analysis.duration}\n")
        
        print("📋 SUMMARY")
        print("-" * 80)
        print(analysis.summary)
        
        # Show word count
        word_count = len(analysis.summary.split())
        print(f"\n[Word count: {word_count} words]")
        
        print("\n\n⏰ KEY TIMESTAMPS")
        print("-" * 80)
        if analysis.key_timestamps:
            for ts in analysis.key_timestamps:
                try:
                    timestamp = ts.get('timestamp', 'N/A')
                    description = ts.get('description', 'N/A')
                    print(f"  [{timestamp}] {description}")
                except Exception as e:
                    print(f"  [Error] Could not parse timestamp: {ts}")
        else:
            print("  No timestamps extracted")
        
        print("\n\n🏷️  MAIN THEMES")
        print("-" * 80)
        if analysis.themes:
            for i, theme in enumerate(analysis.themes, 1):
                print(f"  {i}. {theme}")
        else:
            print("  No themes identified")
        
        print("\n\n📖 CONTENT BREAKDOWN")
        print("-" * 80)
        for section, content in analysis.content_breakdown.items():
            print(f"\n{section.upper().replace('_', ' ')}:")
            print(f"  {content}")
        
        print("\n" + "=" * 80)