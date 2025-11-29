import os
from typing import Optional

# Default to Vertex AI (Enterprise) as the primary fallback
# This can be changed via the AI_DOCFIX_MODEL env var.
DEFAULT_MODEL = "vertex_ai/gemini-1.5-flash-002"

def get_model_name() -> str:
    """
    Get the model identifier for LiteLLM.
    
    Can be overridden via environment variable 'AI_DOCFIX_MODEL'.
    
    Examples:
        - vertex_ai/gemini-1.5-pro
        - gpt-4o
        - claude-3-5-sonnet
        - openai/my-local-model (for LM Studio)
    """
    return os.getenv("AI_DOCFIX_MODEL", DEFAULT_MODEL)

def get_api_base() -> Optional[str]:
    """
    Get custom API base URL.
    
    Required for local inference tools like LM Studio or Ollama.
    Set 'AI_DOCFIX_BASE_URL' to e.g. 'http://localhost:1234/v1'.
    """
    return os.getenv("AI_DOCFIX_BASE_URL", None)

def get_generation_config() -> dict:
    """
    Get standard generation parameters.
    """
    return {
        "temperature": 0.2,  # Low temperature for factual docstrings
        "max_tokens": 500,   # Limit length to prevent hallucinations
        "top_p": 0.8,
    }