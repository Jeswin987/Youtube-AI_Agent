"""
Video analyzer - contains all analysis logic
"""

import json
import re
from typing import Dict, List
from llm_provider import LLMProvider
from config import Config
from youtube_service import YouTubeService


class VideoAnalyzer:
    """Performs AI-powered video analysis"""
    
    def __init__(self, llm: LLMProvider):
        """
        Initialize analyzer with LLM provider
        
        Args:
            llm: LLMProvider instance
        """
        self.llm = llm
    
    def generate_summary(self, transcript_text: str, word_count: str = None) -> str:
        """
        Generate video summary with dynamic word count and enforcement
        
        Args:
            transcript_text: Formatted transcript text
            word_count: Target word count (e.g., "200-300"). Uses config default if None.
        
        Returns:
            Generated summary text
        """
        if word_count is None:
            word_count = Config.SUMMARY_WORD_COUNT
        
        # Parse target range
        try:
            target_min, target_max = map(int, word_count.split('-'))
        except:
            target_min, target_max = 250, 350  # Fallback
        
        system_prompt = """You are an expert at summarizing video content. 
You MUST follow the exact word count requirement. This is absolutely critical.
Count your words carefully before submitting your response."""
        
        prompt = f"""Analyze this YouTube video transcript and provide a comprehensive summary.

STRICT REQUIREMENT: Your summary MUST be between {target_min} and {target_max} words.
This is mandatory. If you write less than {target_min} words, you FAIL the task.

The summary should:
- Cover all major topics and key points discussed
- Include important examples, data, and insights
- Maintain clear, flowing narrative structure
- Provide meaningful context and details
- Be EXACTLY within the {target_min}-{target_max} word range

Transcript:
{transcript_text[:Config.MAX_TRANSCRIPT_LENGTH]}

Write your comprehensive {target_min}-{target_max} word summary now:"""
        
        summary = self.llm.generate(prompt, system_prompt)
        
        # Word count validation
        words = summary.split()
        actual_count = len(words)
        
        if Config.DEBUG_MODE:
            print(f"[DEBUG] Initial summary: {actual_count} words (target: {word_count})")
        
        # If significantly under target, try to expand
        if actual_count < target_min * 0.75:  # Less than 75% of minimum
            if Config.DEBUG_MODE:
                print(f"[DEBUG] Summary too short ({actual_count}/{target_min} min), requesting expansion...")
            
            expand_prompt = f"""The previous summary was only {actual_count} words but MUST be {target_min}-{target_max} words.

Expand this summary significantly by:
- Adding more specific details and examples
- Including additional context and background
- Elaborating on key points mentioned
- Providing more comprehensive coverage

Original summary:
{summary}

Write expanded summary (MUST be {target_min}-{target_max} words):"""
            
            try:
                summary = self.llm.generate(expand_prompt, system_prompt)
                words = summary.split()
                actual_count = len(words)
                if Config.DEBUG_MODE:
                    print(f"[DEBUG] After expansion: {actual_count} words")
            except:
                if Config.DEBUG_MODE:
                    print("[DEBUG] Expansion failed, keeping original")
        
        # If over target, trim intelligently
        if actual_count > target_max * Config.WORD_COUNT_TRIM_THRESHOLD:
            if Config.DEBUG_MODE:
                print(f"[DEBUG] Summary too long ({actual_count} words), trimming to ~{target_max}")
            
            # Trim to target length
            trimmed = ' '.join(words[:target_max])
            
            # Try to end on a complete sentence
            last_period = trimmed.rfind('.')
            last_exclamation = trimmed.rfind('!')
            last_question = trimmed.rfind('?')
            last_sentence_end = max(last_period, last_exclamation, last_question)
            
            # Only use sentence boundary if we retain enough content
            if last_sentence_end > target_max * Config.MIN_SUMMARY_RETENTION:
                summary = trimmed[:last_sentence_end + 1]
            else:
                summary = trimmed + '...'
            
            actual_count = len(summary.split())
        
        if Config.DEBUG_MODE:
            print(f"[DEBUG] Final summary: {actual_count} words (target: {word_count})")
        
        return summary
    
    def extract_timestamps_simple(self, transcript_text: str) -> List[Dict[str, str]]:
        """Extract timestamps by sampling transcript at regular intervals"""
        
        # Parse formatted transcript
        transcript_lines = transcript_text.split('\n')
        transcript_entries = []
        
        for line in transcript_lines:
            match = re.match(r'\[(\d{1,2}:\d{2})\]\s*(.+)', line)
            if match:
                transcript_entries.append({
                    'timestamp': match.group(1),
                    'text': match.group(2)
                })
        
        if not transcript_entries:
            if Config.DEBUG_MODE:
                print("[DEBUG] No transcript entries found for timestamp extraction")
            return []
        
        total = len(transcript_entries)
        if Config.DEBUG_MODE:
            print(f"[DEBUG] Found {total} transcript entries")
        
        # Sample 7-8 key points throughout the video
        sample_points = [
            (0, "Video introduction"),
            (total // 6, "Early discussion"),
            (total // 3, "First main topic"),
            (total // 2, "Mid-point discussion"),
            (2 * total // 3, "Second main topic"),
            (5 * total // 6, "Late discussion"),
            (total - 1, "Conclusion and wrap-up")
        ]
        
        timestamps = []
        for idx, default_desc in sample_points:
            if idx < len(transcript_entries):
                entry = transcript_entries[idx]
                # Use the actual transcript text as description
                description = entry['text'][:80]  # First 80 chars
                timestamps.append({
                    'timestamp': entry['timestamp'],
                    'description': description
                })
        
        if Config.DEBUG_MODE:
            print(f"[DEBUG] Extracted {len(timestamps)} timestamps")
        return timestamps
    
    def identify_themes(self, transcript_text: str) -> List[str]:
        """Identify main themes with better cleaning"""
        system_prompt = "You are an expert at identifying themes and topics in content."
        
        prompt = f"""Identify {Config.NUM_THEMES} main themes or topics discussed in this video transcript.

CRITICAL: Respond with ONLY a comma-separated list of themes. 
Do NOT include:
- Introduction phrases like "Here are the themes:"
- Numbering or bullet points
- Explanations or descriptions
- Any other text

Format: Theme1, Theme2, Theme3, Theme4, Theme5

Transcript:
{transcript_text[:Config.MAX_TRANSCRIPT_LENGTH]}

Comma-separated themes only:"""
        
        response = self.llm.generate(prompt, system_prompt)
        
        # Clean up response
        response = response.strip()
        
        # Remove common intro phrases and artifacts
        intro_patterns = [
            r'^Here are the.*?:\s*\n*',
            r'^The themes? (?:are|include):\s*\n*',
            r'^Themes?:\s*\n*',
            r'^Main topics?:\s*\n*',
            r'^\d+\.\s*',
            r'^-\s*',
            r'^\*\s*'
        ]
        
        for pattern in intro_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE | re.MULTILINE)
        
        # Split by commas or newlines
        if ',' in response:
            themes = [theme.strip() for theme in response.split(',')]
        else:
            # If no commas, try splitting by newlines
            themes = [theme.strip() for theme in response.split('\n')]
        
        # Clean each theme
        cleaned_themes = []
        for theme in themes:
            # Remove numbering, bullets, dashes
            theme = re.sub(r'^\d+[\.\)]\s*', '', theme)
            theme = re.sub(r'^[-\*]\s*', '', theme)
            theme = theme.strip()
            
            # Remove quotes
            theme = theme.strip('"\'')
            
            # Only keep if it's substantial
            if theme and len(theme) > 3 and not theme.lower().startswith('here'):
                cleaned_themes.append(theme)
        
        # Return up to 5 themes
        result = cleaned_themes[:5]
        
        if Config.DEBUG_MODE:
            print(f"[DEBUG] Identified {len(result)} themes: {result}")
        
        return result
    
    def create_content_breakdown(self, transcript_text: str) -> Dict[str, str]:
        """Create structured content breakdown with AI-powered fallback"""
        
        # First attempt: Strong JSON-only prompt
        system_prompt = """You are an expert video analyst. You MUST respond with ONLY a valid JSON object.
Do NOT include markdown, code blocks, or any other text. Just the raw JSON."""
        
        prompt = f"""Analyze this video transcript and create a breakdown with three sections.

Respond with ONLY this JSON (no markdown, no ```):
{{
  "introduction": "2-3 complete sentences describing the video's opening and main topic",
  "main_content": "3-4 complete sentences covering the key points, discussions, and important moments",
  "conclusion": "2-3 complete sentences about the ending, final thoughts, and takeaways"
}}

Make sure all sentences are complete and well-written.

Transcript (first part):
{transcript_text[:5000]}

Middle section:
{transcript_text[len(transcript_text)//2:len(transcript_text)//2 + 3000]}

End section:
{transcript_text[-3000:]}

JSON only:"""
        
        response = self.llm.generate(prompt, system_prompt)
        
        if Config.DEBUG_MODE:
            print(f"[DEBUG] Content breakdown response (first 200 chars): {response[:200]}")
        
        # Clean response
        response = response.strip()
        response = re.sub(r'^```json\s*', '', response)
        response = re.sub(r'^```\s*', '', response)
        response = re.sub(r'```\s*$', '', response)
        
        # Try to parse JSON
        try:
            # Multiple extraction attempts
            json_match = re.search(r'\{[^{}]*"introduction"[^{}]*"main_content"[^{}]*"conclusion"[^{}]*\}', 
                                  response, re.DOTALL)
            
            if not json_match:
                json_match = re.search(r'\{.*?"introduction".*?\}', response, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                
                if all(key in result for key in ['introduction', 'main_content', 'conclusion']):
                    # Validate content quality - check for complete sentences
                    if all(len(result[key]) > 50 and result[key].strip().endswith(('.', '!', '?')) 
                          for key in ['introduction', 'main_content', 'conclusion']):
                        if Config.DEBUG_MODE:
                            print("[DEBUG] Successfully parsed high-quality content breakdown")
                        return result
                    else:
                        if Config.DEBUG_MODE:
                            print("[DEBUG] JSON parsed but content quality low, trying prose fallback")
        
        except Exception as e:
            if Config.DEBUG_MODE:
                print(f"[DEBUG] JSON parsing failed: {e}, trying prose fallback")
        
        # Fallback: Use AI to generate prose description
        if Config.DEBUG_MODE:
            print("[DEBUG] Using AI-powered prose fallback for content breakdown")
        
        return self._generate_prose_breakdown(transcript_text)
    
    def _generate_prose_breakdown(self, transcript_text: str) -> Dict[str, str]:
        """Generate content breakdown using simpler AI prompt (fallback method)"""
        
        system_prompt = "You are an expert at analyzing video content. Write clear, complete sentences."
        
        try:
            # Get introduction
            intro_prompt = f"""Based on this video opening, write 2-3 complete sentences describing what the video is about.

Opening transcript:
{transcript_text[:3000]}

Write 2-3 complete sentences:"""
            
            introduction = self.llm.generate(intro_prompt, system_prompt).strip()
            
            # Clean up introduction
            if not introduction.endswith(('.', '!', '?')):
                last_period = max(introduction.rfind('.'), introduction.rfind('!'), introduction.rfind('?'))
                if last_period > 0:
                    introduction = introduction[:last_period + 1]
            
            # Get main content
            middle_start = len(transcript_text) // 3
            middle_end = 2 * len(transcript_text) // 3
            
            main_prompt = f"""Based on this video middle section, write 3-4 complete sentences describing the main topics and discussions.

Middle transcript:
{transcript_text[middle_start:middle_end][:4000]}

Write 3-4 complete sentences:"""
            
            main_content = self.llm.generate(main_prompt, system_prompt).strip()
            
            # Clean up main content
            if not main_content.endswith(('.', '!', '?')):
                last_period = max(main_content.rfind('.'), main_content.rfind('!'), main_content.rfind('?'))
                if last_period > 0:
                    main_content = main_content[:last_period + 1]
            
            # Get conclusion
            conclusion_prompt = f"""Based on this video ending, write 2-3 complete sentences describing the conclusion and final takeaways.

Ending transcript:
{transcript_text[-3000:]}

Write 2-3 complete sentences:"""
            
            conclusion = self.llm.generate(conclusion_prompt, system_prompt).strip()
            
            # Clean up conclusion
            if not conclusion.endswith(('.', '!', '?')):
                last_period = max(conclusion.rfind('.'), conclusion.rfind('!'), conclusion.rfind('?'))
                if last_period > 0:
                    conclusion = conclusion[:last_period + 1]
            
            # Validate quality
            if len(introduction) < 30 or len(main_content) < 50 or len(conclusion) < 30:
                raise ValueError("Generated content too short")
            
            if Config.DEBUG_MODE:
                print("[DEBUG] Successfully generated prose breakdown")
            
            return {
                "introduction": introduction,
                "main_content": main_content,
                "conclusion": conclusion
            }
        
        except Exception as e:
            if Config.DEBUG_MODE:
                print(f"[DEBUG] Prose generation failed: {e}, using smart text extraction")
            
            # Final fallback: Smart text extraction
            return self._smart_text_extraction(transcript_text)
    
    def _smart_text_extraction(self, transcript_text: str) -> Dict[str, str]:
        """Extract meaningful text from transcript as last resort fallback"""
        
        lines = transcript_text.split('\n')
        total_lines = len(lines)
        
        # Helper function to clean transcript lines
        def clean_lines(line_list):
            """Extract clean text from transcript lines"""
            cleaned = []
            for line in line_list:
                if ']' in line:
                    text = line.split(']', 1)[1].strip()
                else:
                    text = line.strip()
                if text and len(text) > 10:  # Filter out very short lines
                    cleaned.append(text)
            return cleaned
        
        # Get introduction (first 3% of video)
        intro_end = max(30, int(total_lines * 0.03))
        intro_lines = clean_lines(lines[:intro_end])
        intro_text = ' '.join(intro_lines[:15])  # First 15 meaningful lines
        
        # Add proper ending if cut off
        if intro_text and not intro_text.endswith(('.', '!', '?')):
            last_period = intro_text.rfind('.')
            last_question = intro_text.rfind('?')
            last_exclaim = intro_text.rfind('!')
            last_sentence = max(last_period, last_question, last_exclaim)
            
            if last_sentence > len(intro_text) * 0.6:
                intro_text = intro_text[:last_sentence + 1]
            else:
                intro_text += "."
        
        # Get middle section (40-60% of video)
        middle_start = int(total_lines * 0.4)
        middle_end = int(total_lines * 0.6)
        middle_lines = clean_lines(lines[middle_start:middle_end])
        
        # Sample middle section intelligently
        sample_size = min(20, len(middle_lines))
        if len(middle_lines) > sample_size:
            step = len(middle_lines) // sample_size
            sampled = [middle_lines[i] for i in range(0, len(middle_lines), step)][:sample_size]
        else:
            sampled = middle_lines
        
        middle_text = ' '.join(sampled)
        
        # Clean up middle text
        if middle_text and not middle_text.endswith(('.', '!', '?')):
            last_sentence = max(middle_text.rfind('.'), middle_text.rfind('?'), middle_text.rfind('!'))
            if last_sentence > len(middle_text) * 0.6:
                middle_text = middle_text[:last_sentence + 1]
            else:
                middle_text += "."
        
        # Get conclusion (last 3% of video)
        end_start = int(total_lines * 0.97)
        end_lines = clean_lines(lines[end_start:])
        end_text = ' '.join(end_lines[:15])
        
        # Clean up conclusion
        if end_text and not end_text.endswith(('.', '!', '?')):
            last_sentence = max(end_text.rfind('.'), end_text.rfind('?'), end_text.rfind('!'))
            if last_sentence > len(end_text) * 0.6:
                end_text = end_text[:last_sentence + 1]
            else:
                end_text += "."
        
        # Final validation and defaults
        intro_final = intro_text if len(intro_text) > 50 else "The video begins by introducing the main topic and setting the context for the discussion."
        main_final = middle_text if len(middle_text) > 80 else "The video covers the main points and key concepts through detailed discussion and examples."
        end_final = end_text if len(end_text) > 50 else "The video concludes by summarizing the key takeaways and final thoughts on the topic."
        
        if Config.DEBUG_MODE:
            print("[DEBUG] Used smart text extraction fallback")
        
        return {
            "introduction": intro_final,
            "main_content": main_final,
            "conclusion": end_final
        }