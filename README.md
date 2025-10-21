# 🎬 YouTube Analysis Agent

An intelligent AI agent that autonomously analyzes YouTube videos, generating comprehensive summaries, timestamps, themes, and content breakdowns.

---

## ✨ Features

- **Smart Summaries** – AI-generated summaries with dynamic length based on video duration (100–600 words)
- **Key Timestamps** – Extracts 7 important moments throughout the video
- **Theme Identification** – Identifies 3–5 main topics discussed
- **Content Breakdown** – Structured analysis (Introduction, Main Content, Conclusion)
- **Autonomous Fallback** – Works on videos with or without captions
- **Whisper Integration** – Automatic speech-to-text transcription when captions are unavailable

---

## 🤖 Agentic AI Capabilities

This isn’t just a static app — it’s an **autonomous AI agent** that:

- 🧠 **Makes Decisions** – Chooses between captions and Whisper transcription
- ⚙️ **Adapts Strategy** – Adjusts summary length based on video duration
- 🔁 **Self-Corrects** – Built-in fallback ensures reliable output
- 🪄 **Orchestrates Tools** – Coordinates YouTube API, Whisper AI, and LLM services

---

## 🏗️ Project Architecture


├── config.py # Configuration and settings
├── models.py # Data structures (VideoMetadata, VideoAnalysis)
├── llm_provider.py # LLM integration (Google Gemini/Ollama/Groq)
├── youtube_service.py # YouTube data extraction
├── whisper_service.py # Audio transcription (OpenAI Whisper)
├── analyzer.py # AI analysis logic
├── agent.py # Main agent orchestrator
├── main.py # CLI entry point
├── requirements.txt # Python dependencies
└── README.md # Documentation (this file)


---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- ffmpeg (for Whisper audio processing)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Jeswin987/Youtube-AI_Agent
   cd youtube-analysis-agent
pip install -r requirements.txt
Install ffmpeg:


Download from gyan.dev/ffmpeg/builds

Extract and add to PATH

Add your API key in config.py:

LLM_PROVIDER = "google"  # or "ollama"
GOOGLE_API_KEY = "your_api_key_here"


👉 Get a free key from: https://aistudio.google.com/app/apikey

Run the app:

python main.py


Enter a YouTube URL when prompted, and the agent will automatically analyze the video.

📺 VIDEO ANALYSIS: Introduction to Machine Learning
⏱️ Duration: 18.3 minutes

📋 SUMMARY
This video provides a comprehensive introduction to machine learning...
[342 words]

⏰ KEY TIMESTAMPS
[00:00] Introduction to the course
[03:15] What is Machine Learning
[07:45] Types of ML algorithms
[12:30] Real-world applications
[16:45] Getting started with ML

🏷️ MAIN THEMES
1. Machine Learning Fundamentals
2. Supervised vs Unsupervised Learning
3. Practical Applications
4. Getting Started Resources

📖 CONTENT BREAKDOWN
**Introduction:** The video opens by explaining the growing importance...
**Main Content:** The presenter discusses three main types of machine learning...
**Conclusion:** The video concludes with practical advice for beginners...

🧠 How It Works
Autonomous Workflow

Extract video ID from URL

Fetch metadata (title, duration, author)

Get transcript automatically:

Try YouTube captions (fast)

If unavailable → use Whisper AI (fallback)

Analyze video content using LLM

Generate structured output (summary, timestamps, themes, breakdown)

Key Agentic Behaviors

Decision 1 – Transcript Method

if captions_available:
    use_captions()
else:
    use_whisper()


Decision 2 – Summary Length

if video_duration < 5:
    summary_length = "100-150 words"
elif video_duration < 20:
    summary_length = "300-400 words"


Decision 3 – Error Recovery

try:
    parse_json_response()
except:
    try_alternative_method()

🛠️ Tech Stack

Language: Python 3.8+

AI/LLM: Google Gemini (Gemini 1.5 Flash)

Speech Recognition: OpenAI Whisper

YouTube API: YouTube Transcript API, yt-dlp

Data Handling: JSON, Regex, TextBlob

📈 Performance
Metric	Description
⏱️ Processing Time	30–60 seconds per video
✅ Success Rate	100% (works with or without captions)
📹 Video Length Supported	5 – 60+ minutes
💰 Cost	Free (uses free API tiers)
⚙️ Configuration

Edit config.py as needed:

LLM_PROVIDER = "google"  # Options: google, ollama, groq
DYNAMIC_WORD_COUNT_RULES = {
    5: "100-150",
    10: "200-300",
    20: "300-400",
    40: "400-500",
    999: "500-600"
}
MAX_TRANSCRIPT_LENGTH = 15000
TEMPERATURE = 0.7

🎯 Use Cases

🎓 Students – Quickly summarize lecture videos

🧑‍🔬 Researchers – Analyze academic talks & interviews

🎥 Creators – Generate timestamps & video descriptions

🧏 Accessibility – Create transcripts for videos without captions

💼 Professionals – Extract insights from webinars and conferences

🚧 Limitations

Currently supports English only

Whisper transcription can be slow for long videos

Summary quality depends on audio clarity

Internet connection required for API calls

🔮 Future Enhancements

 🌍 Multi-language support

 📜 Batch processing for playlists

 ❤️ Sentiment analysis

 🔑 Keyword extraction

 🧾 Export results to PDF/Markdown

📝 License

MIT License — feel free to use, modify, or share for personal and educational purposes.

👤 Author

Jesvin Devasia

GitHub: @https://github.com/Jeswin987


🙏 Acknowledgments

OpenAI Whisper
 for speech recognition

Google Gemini AI
 for text understanding

YouTube Transcript API
 for caption extraction

📚 Documentation

Architecture Guide
 (optional)

API Reference
 (optional)



