"""
LLM Provider integration - handles Groq and Ollama
"""

import requests
from typing import Optional
from config import Config


class LLMProvider:
    """Handles LLM API calls for both Groq and Ollama"""
    
    def __init__(self, provider: str = None, api_key: Optional[str] = None):
        """
        Initialize LLM Provider
        
        Args:
            provider: 'groq' or 'ollama' (defaults to Config.LLM_PROVIDER)
            api_key: API key for Groq (defaults to Config.GROQ_API_KEY)
        """
        self.provider = provider or Config.LLM_PROVIDER
        self.api_key = api_key or Config.GROQ_API_KEY
        
        if self.provider == "groq" and not self.api_key:
            raise ValueError("API key required for Groq. Get free key at: https://console.groq.com")
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            
        Returns:
            Generated text response
        """
        if self.provider == "groq":
            return self._call_groq(prompt, system_prompt)
        elif self.provider == "ollama":
            return self._call_ollama(prompt, system_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _call_groq(self, prompt: str, system_prompt: str) -> str:
        """Call Groq API"""
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

            if Config.DEBUG_MODE:
                print(f"[DEBUG] Groq API response status: {response.status_code}")

            if response.status_code != 200:
                error_detail = response.json() if response.content else "No details"
                print(f"[ERROR] Groq  error: {error_detail}")
                raise Exception(f"Groq API error: {response.status_code} - {error_detail}")
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        
        except requests.exceptions.Timeout:
            raise Exception("Groq API request timed out. Try again ")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Groq API request failed: {str(e)}")

        
    
    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        """Call local Ollama API"""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        data = {
            "model": Config.OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False
        }
        
        response = requests.post(Config.OLLAMA_URL, json=data)
        response.raise_for_status()
        return response.json()["response"]

