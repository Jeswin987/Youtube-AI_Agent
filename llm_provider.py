"""
LLM Provider integration - handles Google, Groq, and Ollama
"""

import requests
import google.generativeai as genai
from typing import Optional
from config import Config


class LLMProvider:
    """Handles LLM API calls for Google, Groq, and Ollama"""

    def __init__(self, provider: str = None, api_key: Optional[str] = None):
        """
        Initialize LLM Provider

        Args:
            provider: 'google', 'groq', or 'ollama' (defaults to Config.LLM_PROVIDER)
            api_key: API key for selected provider (defaults to Config.*_API_KEY)
        """
        self.provider = provider or Config.LLM_PROVIDER

        # Select API key based on provider
        if self.provider == "google":
            self.api_key = api_key or Config.GOOGLE_API_KEY
        elif self.provider == "groq":
            self.api_key = api_key or Config.GROQ_API_KEY
        else:
            self.api_key = None

        # Validate
        if self.provider == "google" and not self.api_key:
            raise ValueError("Google API key is missing. Set it in .env or Config.")
        if self.provider == "groq" and not self.api_key:
            raise ValueError("Groq API key is missing. Get one at https://console.groq.com")

        # Initialize Google GenAI if applicable
        if self.provider == "google":
            genai.configure(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate response from LLM

        Args:
            prompt: User prompt
            system_prompt: System instructions

        Returns:
            Generated text response
        """
        if self.provider == "google":
            return self._call_google(prompt, system_prompt)
        elif self.provider == "groq":
            return self._call_groq(prompt, system_prompt)
        elif self.provider == "ollama":
            return self._call_ollama(prompt, system_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _call_google(self, prompt: str, system_prompt: str) -> str:
        """Call Google Gemini API"""
        model = genai.GenerativeModel(Config.GOOGLE_MODEL)
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = model.generate_content(full_prompt)
            if Config.DEBUG_MODE:
                print("[DEBUG] Google Gemini API call successful")
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Google Gemini API request failed: {e}")

    def _call_groq(self, prompt: str, system_prompt: str) -> str:
        """Call Groq API (for fallback if needed)"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        data = {
            "model": Config.GROQ_MODEL,
            "messages": messages,
            "temperature": Config.TEMPERATURE,
            "max_tokens": Config.MAX_TOKENS,
            "top_p": 1,
            "stream": False
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"Groq API request failed: {e}")

    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        """Call local Ollama API"""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        data = {
            "model": Config.OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False
        }
        try:
            response = requests.post(Config.OLLAMA_URL, json=data)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise Exception(f"Ollama API request failed: {e}")
