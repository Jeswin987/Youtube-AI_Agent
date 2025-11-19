
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from datetime import datetime


from youtube_service import YouTubeService
from whisper_service import WhisperService
from llm_provider import LLMProvider
from analyzer import VideoAnalyzer
from config import Config


class YouTubeSummarizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Summarizer 🎬")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        
        self.whisper_service = None
        self.llm_provider = None
        self.video_analyzer = None
        self.current_analysis = None
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create all GUI elements"""
        
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        
        title_label = ttk.Label(
            main_frame, 
            text="🤖 YouTube Video Summarizer AI Agent", 
            font=("Arial", 18, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        
        url_frame = ttk.LabelFrame(main_frame, text="Enter YouTube URL", padding="10")
        url_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_frame, font=("Arial", 11))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.url_entry.insert(0, "https://youtube.com/watch?v=...")
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<Return>", lambda e: self.start_summarization())
        
        self.summarize_btn = ttk.Button(
            url_frame, 
            text="Summarize 🚀", 
            command=self.start_summarization,
            width=15
        )
        self.summarize_btn.grid(row=0, column=1)
        
        
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        
        self.use_whisper_var = tk.BooleanVar(value=True)
        whisper_check = ttk.Checkbutton(
            options_frame,
            text="🎤 Use Whisper AI fallback (for videos without captions)",
            variable=self.use_whisper_var
        )
        whisper_check.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        
        self.show_timestamps_var = tk.BooleanVar(value=True)
        timestamps_check = ttk.Checkbutton(
            options_frame,
            text="⏱️ Include key timestamps",
            variable=self.show_timestamps_var
        )
        timestamps_check.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        
        self.show_themes_var = tk.BooleanVar(value=True)
        themes_check = ttk.Checkbutton(
            options_frame,
            text="🏷️ Extract main themes",
            variable=self.show_themes_var
        )
        themes_check.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            mode='indeterminate',
            length=400
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.status_label = ttk.Label(
            progress_frame, 
            text=f"Ready to summarize videos 📹 | Using: {Config.LLM_PROVIDER.upper()} ({Config.GOOGLE_MODEL})",
            font=("Arial", 9)
        )
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Console Output Section
        console_frame = ttk.LabelFrame(main_frame, text="Console Output", padding="10")
        console_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        self.console_output = scrolledtext.ScrolledText(
            console_frame,
            height=8,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#00ff00"
        )
        self.console_output.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Summary Output Section (with tabs)
        summary_frame = ttk.LabelFrame(main_frame, text="Analysis Results", padding="10")
        summary_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=2)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(summary_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Summary tab
        summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(summary_tab, text="📝 Summary")
        
        self.summary_output = scrolledtext.ScrolledText(
            summary_tab,
            font=("Arial", 10),
            wrap=tk.WORD
        )
        self.summary_output.pack(fill=tk.BOTH, expand=True)
        
        # Full Analysis tab
        analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(analysis_tab, text="📊 Full Analysis")
        
        self.analysis_output = scrolledtext.ScrolledText(
            analysis_tab,
            font=("Arial", 10),
            wrap=tk.WORD
        )
        self.analysis_output.pack(fill=tk.BOTH, expand=True)
        
        # Buttons Section
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="📋 Copy Summary",
            command=self.copy_summary
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="💾 Save Analysis",
            command=self.save_analysis
        ).grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame,
            text="🗑️ Clear All",
            command=self.clear_all
        ).grid(row=0, column=2, padx=5)
        
    def clear_placeholder(self, event):
        """Clear placeholder text on focus"""
        if self.url_entry.get() == "https://youtube.com/watch?v=...":
            self.url_entry.delete(0, tk.END)
    
    def log_to_console(self, message):
        """Add message to console output"""
        self.console_output.insert(tk.END, message + "\n")
        self.console_output.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def start_summarization(self):
        """Start summarization in a separate thread"""
        url = self.url_entry.get().strip()
        
        if not url or url == "https://youtube.com/watch?v=...":
            messagebox.showwarning("Invalid URL", "Please enter a valid YouTube URL")
            return
        
        # Disable button during processing
        self.summarize_btn.config(state='disabled')
        self.progress_bar.start()
        
        # Clear previous outputs
        self.console_output.delete(1.0, tk.END)
        self.summary_output.delete(1.0, tk.END)
        self.analysis_output.delete(1.0, tk.END)
        
        # Run in separate thread to keep GUI responsive
        thread = threading.Thread(target=self.process_video, args=(url,))
        thread.daemon = True
        thread.start()
    
    def process_video(self, url):
        """Process the video (runs in separate thread)"""
        try:
            # Initialize LLM and Analyzer if not done
            if not self.llm_provider:
                self.log_to_console(f"🤖 Initializing {Config.LLM_PROVIDER.upper()} AI...")
                self.llm_provider = LLMProvider()
                self.video_analyzer = VideoAnalyzer(self.llm_provider)
                self.log_to_console("✓ AI initialized\n")
            
            # Step 1: Get video metadata
            self.update_status("📊 Fetching video metadata...")
            self.log_to_console("📊 Fetching video metadata...")
            
            video_id = YouTubeService.extract_video_id(url)
            metadata = YouTubeService.get_video_metadata(url)
            
            self.log_to_console(f"✓ Video: {metadata.title}")
            self.log_to_console(f"  Duration: {metadata.duration}")
            self.log_to_console(f"  Author: {metadata.author}")
            self.log_to_console(f"  Views: {metadata.views}\n")
            
            # Step 2: Get transcript
            self.update_status("📝 Fetching transcript...")
            self.log_to_console("📝 Attempting to fetch YouTube captions...")
            
            transcript = None
            transcript_method = "YouTube Captions"
            
            try:
                transcript_data = YouTubeService.get_transcript(video_id)
                transcript = YouTubeService.format_transcript(transcript_data)
                self.log_to_console("✓ Captions retrieved successfully!\n")
            except Exception as e:
                self.log_to_console(f"⚠️  No captions available\n")
                
                # Fallback to Whisper if enabled
                if self.use_whisper_var.get():
                    self.log_to_console("="*70)
                    self.log_to_console("🤖 AGENT AUTONOMOUS DECISION:")
                    self.log_to_console("   Captions failed → Switching to Whisper AI transcription")
                    self.log_to_console("   (This demonstrates true agentic behavior!)")
                    self.log_to_console("="*70 + "\n")
                    
                    self.update_status("🎤 Transcribing with Whisper AI (may take several minutes)...")
                    
                    # Lazy load Whisper
                    if not self.whisper_service:
                        self.log_to_console("🎤 Loading Whisper model...")
                        self.whisper_service = WhisperService(model_size="base")
                    
                    self.log_to_console("📥 Downloading audio and transcribing...")
                    transcript_data = self.whisper_service.transcribe_video(video_id)
                    transcript = YouTubeService.format_transcript(transcript_data)
                    transcript_method = "Whisper AI"
                    self.log_to_console("✓ Whisper transcription complete!\n")
                else:
                    raise Exception("No captions available and Whisper is disabled")
            
            # Step 3: Generate summary
            self.update_status("🤖 Generating AI summary...")
            self.log_to_console("🤖 Analyzing video and generating summary...")
            
            summary = self.video_analyzer.generate_summary(transcript)
            self.log_to_console(f"✓ Summary generated ({len(summary.split())} words)\n")
            
            # Step 4: Extract timestamps (optional)
            timestamps = []
            if self.show_timestamps_var.get():
                self.update_status("⏱️ Extracting key timestamps...")
                self.log_to_console("⏱️ Extracting key timestamps...")
                timestamps = self.video_analyzer.extract_timestamps_simple(transcript)
                self.log_to_console(f"✓ Found {len(timestamps)} key moments\n")
            
            # Step 5: Identify themes (optional)
            themes = []
            if self.show_themes_var.get():
                self.update_status("🏷️ Identifying main themes...")
                self.log_to_console("🏷️ Identifying main themes...")
                themes = self.video_analyzer.identify_themes(transcript)
                self.log_to_console(f"✓ Identified {len(themes)} themes\n")
            
            # Step 6: Create content breakdown
            self.update_status("📊 Creating content breakdown...")
            self.log_to_console("📊 Creating structured breakdown...")
            breakdown = self.video_analyzer.create_content_breakdown(transcript)
            self.log_to_console("✓ Breakdown complete\n")
            
            # Format and display results
            self.display_results(metadata, summary, timestamps, themes, breakdown, transcript_method)
            
            self.update_status("✅ Complete! Video analysis ready")
            self.log_to_console("="*70)
            self.log_to_console("✅ VIDEO ANALYSIS COMPLETE!")
            self.log_to_console("="*70)
            messagebox.showinfo("Success", "Video analyzed successfully! 🎉")
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.log_to_console(error_msg)
            self.update_status("❌ Failed to process video")
            messagebox.showerror("Error", str(e))
        
        finally:
            # Re-enable button and stop progress bar
            self.summarize_btn.config(state='normal')
            self.progress_bar.stop()
    
    def display_results(self, metadata, summary, timestamps, themes, breakdown, method):
        """Display formatted results in both tabs"""
        
        # Summary tab - Simple view
        summary_text = f"""
{'='*70}
VIDEO SUMMARY
{'='*70}

📹 Title: {metadata.title}
👤 Author: {metadata.author}
⏱️  Duration: {metadata.duration}
👁️  Views: {metadata.views}
🔧 Transcription: {method}

{'='*70}
SUMMARY
{'='*70}

{summary}
"""
        
        if themes:
            summary_text += f"\n\n{'='*70}\n🏷️  MAIN THEMES\n{'='*70}\n\n"
            for i, theme in enumerate(themes, 1):
                summary_text += f"{i}. {theme}\n"
        
        if timestamps:
            summary_text += f"\n\n{'='*70}\n⏱️  KEY TIMESTAMPS\n{'='*70}\n\n"
            for ts in timestamps:
                summary_text += f"[{ts['timestamp']}] {ts['description']}\n"
        
        self.summary_output.insert(1.0, summary_text)
        
        # Full Analysis tab - Detailed view
        analysis_text = f"""
{'='*70}
COMPLETE VIDEO ANALYSIS
{'='*70}

📹 VIDEO INFORMATION
{'='*70}
Title: {metadata.title}
Author: {metadata.author}
Duration: {metadata.duration}
Views: {metadata.views}
Transcription Method: {method}

{'='*70}
📝 EXECUTIVE SUMMARY
{'='*70}

{summary}

{'='*70}
📊 CONTENT BREAKDOWN
{'='*70}

Introduction:
{breakdown.get('introduction', 'N/A')}

Main Content:
{breakdown.get('main_content', 'N/A')}

Conclusion:
{breakdown.get('conclusion', 'N/A')}
"""
        
        if themes:
            analysis_text += f"\n{'='*70}\n🏷️  MAIN THEMES\n{'='*70}\n\n"
            for i, theme in enumerate(themes, 1):
                analysis_text += f"{i}. {theme}\n"
        
        if timestamps:
            analysis_text += f"\n{'='*70}\n⏱️  KEY TIMESTAMPS\n{'='*70}\n\n"
            for ts in timestamps:
                analysis_text += f"[{ts['timestamp']}] {ts['description']}\n"
        
        analysis_text += f"\n{'='*70}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*70}"
        
        self.analysis_output.insert(1.0, analysis_text)
        
        # Store for saving later
        self.current_analysis = {
            'metadata': metadata,
            'summary': summary,
            'timestamps': timestamps,
            'themes': themes,
            'breakdown': breakdown,
            'method': method
        }
    
    def copy_summary(self):
        """Copy summary to clipboard"""
        summary = self.summary_output.get(1.0, tk.END).strip()
        if summary:
            self.root.clipboard_clear()
            self.root.clipboard_append(summary)
            messagebox.showinfo("Copied", "Summary copied to clipboard!")
        else:
            messagebox.showwarning("Empty", "No summary to copy")
    
    def save_analysis(self):
        """Save full analysis to file"""
        analysis = self.analysis_output.get(1.0, tk.END).strip()
        
        if not analysis:
            messagebox.showwarning("Empty", "No analysis to save")
            return
        
        # Suggest filename based on video title
        suggested_name = "video_analysis.txt"
        if self.current_analysis and 'metadata' in self.current_analysis:
            title = self.current_analysis['metadata'].title
            # Clean title for filename
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
            suggested_name = f"{clean_title}.txt"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=suggested_name,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(analysis)
                messagebox.showinfo("Saved", f"Analysis saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def clear_all(self):
        """Clear all outputs"""
        self.console_output.delete(1.0, tk.END)
        self.summary_output.delete(1.0, tk.END)
        self.analysis_output.delete(1.0, tk.END)
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "https://youtube.com/watch?v=...")
        self.update_status(f"Ready to summarize videos 📹 | Using: {Config.LLM_PROVIDER.upper()}")
        self.current_analysis = None


def main():
    root = tk.Tk()
    app = YouTubeSummarizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()