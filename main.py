"""
Entry point for YouTube Agent
Run this file to analyze videos
"""

import json
from datetime import datetime
from agent import YouTubeAgent


def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 80)
    print("🎬 YOUTUBE VIDEO ANALYZER - AI Agent")
    print("=" * 80)
    print("\nThis AI agent analyzes YouTube videos and provides:")
    print("  ✓ Comprehensive summary")
    print("  ✓ Key timestamps from throughout the video")
    print("  ✓ Main themes and topics")
    print("  ✓ Structured content breakdown")
    print("\n" + "=" * 80 + "\n")


def validate_youtube_url(url: str) -> bool:
    """Validate if URL is a YouTube URL"""
    if not url:
        return False
    return 'youtube.com' in url or 'youtu.be' in url


def main():
    """Main function with interactive loop"""
    print_banner()
    
    # Initialize agent once
    print("🔧 Initializing AI agent...")
    agent = YouTubeAgent()
    print("✓ Agent ready!\n")
    
    while True:
        # Get URL from user
        youtube_url = input("📺 Enter YouTube URL (or 'quit' to exit): ").strip()
        
        # Check for exit command
        if youtube_url.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Thanks for using YouTube Video Analyzer!")
            break
        
        # Validate URL
        if not validate_youtube_url(youtube_url):
            print("❌ Invalid URL. Please provide a valid YouTube URL.")
            print("   Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ\n")
            continue
        
        try:
            print(f"\n🔍 Analyzing: {youtube_url}\n")
            
            # Analyze video
            analysis = agent.analyze_video(youtube_url)
            
            # Print results
            agent.print_analysis(analysis)
            
            # Save to JSON with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'analysis_{timestamp}.json'
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"\n💾 Analysis saved to {filename}")
            
            # Ask if user wants to analyze another video
            print("\n" + "-" * 80)
            continue_choice = input("\n🔄 Analyze another video? (yes/no): ").strip().lower()
            if continue_choice not in ['yes', 'y', '']:
                print("\n👋 Thanks for using YouTube Video Analyzer!")
                break
            
            print("\n")  # Add spacing before next iteration
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("\n💡 Possible reasons:")
            print("  • Video doesn't have captions/subtitles enabled")
            print("  • Video is private, age-restricted, or unavailable")
            print("  • Invalid URL format")
            print("  • Network connection issues")
            print("\nPlease try again with a different video.\n")
            
            # Ask if user wants to try another URL
            retry = input("🔄 Try another URL? (yes/no): ").strip().lower()
            if retry not in ['yes', 'y']:
                print("\n👋 Thanks for using YouTube Video Analyzer!")
                break
            print("\n")


if __name__ == "__main__":
    main()