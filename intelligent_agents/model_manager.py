#!/usr/bin/env python3
"""
Multi-Model Manager for SIGMA-OS
Supports multiple AI providers with hot-swapping
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json

# AI Provider imports
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    import requests
except ImportError:
    requests = None

from dotenv import load_dotenv
load_dotenv()

class ModelProvider(Enum):
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OLLAMA = "ollama"

@dataclass
class AIModel:
    """Represents an AI model configuration"""
    id: str
    name: str
    provider: str
    model_name: str
    description: str
    capabilities: List[str]
    cost_per_1m: float
    rate_limit: Optional[int]  # requests per day
    api_key_env: str
    available: bool = True
    
    def to_dict(self):
        return asdict(self)

class ModelManager:
    """Manages multiple AI models with automatic failover"""
    
    def __init__(self):
        self.current_thinking_model = None
        self.current_execution_model = None
        self.usage_count = {}
        
        # Define available models
        self.available_models = {
            # Google Gemini Models (Keep main one only)
            "gemini-2.0-flash": AIModel(
                id="gemini-2.0-flash",
                name="Gemini 2.0 Flash Exp",
                provider="google",
                model_name="gemini-2.0-flash-exp",
                description="⚡ Fast AI with vision - Experimental (50/day limit)",
                capabilities=["code", "chat", "vision", "reasoning"],
                cost_per_1m=0.0,
                rate_limit=50,  # EXPERIMENTAL model: 50 RPD, 10 RPM, 250K TPM
                api_key_env="GOOGLE_API_KEY"
            ),
            
            # Groq (Keep main one only)
            "groq-llama-3.3-70b": AIModel(
                id="groq-llama-3.3-70b",
                name="Llama 3.3 70B",
                provider="groq",
                model_name="llama-3.3-70b-versatile",
                description="🚀 Meta's best - ultra-fast (1K/day limit)",
                capabilities=["reasoning", "code", "chat"],
                cost_per_1m=0.0,
                rate_limit=1000,  # FREE tier: 1K RPD, 30 RPM, 12K TPM, 100K TPD
                api_key_env="GROQ_API_KEY"
            ),
            
            # Ollama (Local models - FREE!)
            "ollama-llama3.2": AIModel(
                id="ollama-llama3.2",
                name="Llama 3.2 (Local)",
                provider="ollama",
                model_name="llama3.2",
                description="🏠 Local Meta model - no limits",
                capabilities=["code", "chat"],
                cost_per_1m=0.0,
                rate_limit=None,  # Unlimited - runs locally
                api_key_env=""
            ),
            "ollama-codellama": AIModel(
                id="ollama-codellama",
                name="CodeLlama (Local)",
                provider="ollama",
                model_name="codellama",
                description="💻 Local code specialist - no limits",
                capabilities=["code"],
                cost_per_1m=0.0,
                rate_limit=None,  # Unlimited - runs locally
                api_key_env=""
            ),
            
            # OpenAI (GPT-4, GPT-3.5, etc.)
            "openai-gpt4": AIModel(
                id="openai-gpt4",
                name="GPT-4 Turbo",
                provider="openai",
                model_name="gpt-4-turbo-preview",
                description="🧠 Advanced reasoning and analysis",
                capabilities=["reasoning", "code", "chat", "vision"],
                cost_per_1m=0.01,
                rate_limit=None,
                api_key_env="OPENAI_API_KEY"
            ),
        }
        
        # Check which models are actually available (have API keys)
        self._check_availability()
        
        # Set default models
        self._set_defaults()
    
    def _check_availability(self):
        """Check which models have valid API keys (reads from .env dynamically)"""
        from pathlib import Path
        import re
        
        # Load .env file dynamically to catch recently saved keys
        env_path = Path(__file__).parent.parent / ".env"
        env_vars = {}
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, val = line.split('=', 1)
                        env_vars[key.strip()] = val.strip()
        
        for model_id, model in self.available_models.items():
            if model.api_key_env:
                # Check both os.getenv and .env file
                api_key = env_vars.get(model.api_key_env) or os.getenv(model.api_key_env)
                model.available = bool(api_key and api_key.strip())
            else:
                # Ollama - check if server is running
                if model.provider == "ollama":
                    try:
                        if requests:
                            resp = requests.get("http://localhost:11434/api/tags", timeout=1)
                            model.available = resp.status_code == 200
                        else:
                            model.available = False
                    except:
                        model.available = False
    
    def _set_defaults(self):
        """Set default models based on availability"""
        # Try to set thinking model - prefer Groq Llama 3.3 70B
        for model_id in ["groq-llama-3.3-70b", "gemini-2.0-flash", "ollama-llama3.2"]:
            if model_id in self.available_models and self.available_models[model_id].available:
                self.current_thinking_model = model_id
                break
        
        # Set SAME model for execution (simplicity!)
        self.current_execution_model = self.current_thinking_model
    
    def get_available_models(self) -> List[Dict]:
        """Get list of all available models"""
        return [
            {
                **model.to_dict(),
                "is_thinking_model": model_id == self.current_thinking_model,
                "is_execution_model": model_id == self.current_execution_model
            }
            for model_id, model in self.available_models.items()
        ]
    
    def set_thinking_model(self, model_id: str) -> bool:
        """Set the model used for thinking/planning"""
        if model_id in self.available_models and self.available_models[model_id].available:
            self.current_thinking_model = model_id
            return True
        return False
    
    def set_execution_model(self, model_id: str) -> bool:
        """Set the model used for quick execution"""
        if model_id in self.available_models and self.available_models[model_id].available:
            self.current_execution_model = model_id
            return True
        return False
    
    def get_thinking_model(self):
        """Get configured thinking model client"""
        return self._get_model_client(self.current_thinking_model)
    
    def get_execution_model(self):
        """Get configured execution model client"""
        return self._get_model_client(self.current_execution_model)
    
    def _get_model_client(self, model_id: str):
        """Get actual AI model client"""
        if not model_id or model_id not in self.available_models:
            raise Exception(f"Model {model_id} not available")
        
        model = self.available_models[model_id]
        
        if model.provider == "google":
            if not genai:
                raise Exception("google-generativeai not installed")
            genai.configure(api_key=os.getenv(model.api_key_env))
            return genai.GenerativeModel(
                model.model_name,
                generation_config={
                    "temperature": 1.0 if "thinking" in model_id else 0.7,
                    "top_p": 0.95,
                    "max_output_tokens": 8192,
                }
            )
        
        elif model.provider == "openai":
            if not OpenAI:
                raise Exception("openai not installed")
            return OpenAIWrapper(
                client=OpenAI(api_key=os.getenv(model.api_key_env)),
                model_name=model.model_name
            )
        
        elif model.provider == "anthropic":
            if not Anthropic:
                raise Exception("anthropic not installed")
            return AnthropicWrapper(
                client=Anthropic(api_key=os.getenv(model.api_key_env)),
                model_name=model.model_name
            )
        
        elif model.provider == "groq":
            if not OpenAI:
                raise Exception("openai not installed (needed for Groq)")
            return OpenAIWrapper(
                client=OpenAI(
                    api_key=os.getenv(model.api_key_env),
                    base_url="https://api.groq.com/openai/v1"
                ),
                model_name=model.model_name
            )
        
        elif model.provider == "ollama":
            if not requests:
                raise Exception("requests not installed")
            return OllamaWrapper(model_name=model.model_name)
        
        raise Exception(f"Unknown provider: {model.provider}")
    
    def track_usage(self, model_id: str):
        """Track model usage"""
        self.usage_count[model_id] = self.usage_count.get(model_id, 0) + 1

# Wrapper classes to provide unified interface
class OpenAIWrapper:
    def __init__(self, client, model_name):
        self.client = client
        self.model_name = model_name
    
    def generate_content(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return TextResponse(response.choices[0].message.content)

class AnthropicWrapper:
    def __init__(self, client, model_name):
        self.client = client
        self.model_name = model_name
    
    def generate_content(self, prompt):
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )
        return TextResponse(response.content[0].text)

class OllamaWrapper:
    def __init__(self, model_name):
        self.model_name = model_name
        self.base_url = "http://localhost:11434"
    
    def generate_content(self, prompt):
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model_name, "prompt": prompt, "stream": False}
        )
        return TextResponse(response.json()["response"])

class TextResponse:
    """Unified response object"""
    def __init__(self, text):
        self.text = text

# Global model manager instance
model_manager = ModelManager()
