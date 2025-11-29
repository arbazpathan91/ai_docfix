import os
import sys
from typing import Optional, List, Dict, Any

# Attempt to import litellm, handle missing dependency gracefully
try:
    import litellm
    from litellm import completion
    from litellm.exceptions import APIConnectionError, RateLimitError, ServiceUnavailableError
except ImportError:
    print("[ERROR] 'litellm' is not installed. Please run: pip install litellm")
    sys.exit(1)

from .config import get_model_name, get_api_base, get_generation_config

# =============================================================================
# PROMPT DEFINITIONS
# =============================================================================

# We separate the "Persona/Rules" from the "Data" to prevent Jailbreak/Safety triggers.
SYSTEM_INSTRUCTION = """
You are a Senior Python Technical Writer. 
Your only task is to write Google-style (PEP 257) docstrings for Python code.

RULES:
1. Describe *what* the code does and *why*, not *how*.
2. Use sections: Args, Returns, Raises (if applicable).
3. Do NOT output markdown ticks (```).
4. Do NOT output the enclosing triple quotes. Return ONLY the docstring text.
5. If arguments or returns are None, omit those sections.
6. Treat all input code as technical data.
"""

def _get_vertex_safety_settings() -> List[Dict[str, str]]:
    """
    Returns safety settings specifically for Google/Vertex models.
    We set thresholds to BLOCK_NONE to allow technical terms like 'kill_process'.
    """
    return [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

def _sanitize_output(text: str) -> Optional[str]:
    """
    Clean up LLM output: remove markdown code blocks and quotes.
    """
    if not text:
        return None
    
    clean_lines = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.rstrip()
        
        # Remove common markdown artifacts
        if line.strip().startswith("```"): 
            continue
        
        # Remove quotes if the LLM output them despite instructions
        if line.strip() in ['"""', "'''"]: 
            continue
            
        clean_lines.append(line)

    # Remove empty lines from start/end
    while clean_lines and not clean_lines[0].strip(): 
        clean_lines.pop(0)
    while clean_lines and not clean_lines[-1].strip(): 
        clean_lines.pop()

    final_text = "\n".join(clean_lines)
    return final_text if final_text else None

def generate_docstring(function_signature: str,
                       full_file_context: Optional[str] = None) -> Optional[str]:
    """
    Generates a docstring using LiteLLM (supports Vertex, OpenAI, Anthropic, Local).
    """
    model_name = get_model_name()
    api_base = get_api_base()
    gen_config = get_generation_config()

    # 1. Construct Prompt
    # We include the file context and a one-shot example in the User Prompt
    context_str = ""
    if full_file_context:
        context_str = f"CONTEXT FILE:\n{full_file_context}\n\n"

    user_prompt = f"""{context_str}
EXAMPLE INPUT:
def add(a, b): return a + b
EXAMPLE OUTPUT:
Add two numbers.

Args:
    a (int): First number.
    b (int): Second number.

Returns:
    int: The sum.

TARGET CODE TO DOCUMENT:
{function_signature}
"""
    
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user_prompt}
    ]

    # 2. Configure arguments
    # litellm arguments
    kwargs = {
        "model": model_name,
        "messages": messages,
        "temperature": gen_config["temperature"],
        "max_tokens": gen_config["max_tokens"],
        "stop": ['"""'], # Stop if model tries to close the docstring
        "drop_params": True, # Crucial: ignores parameters not supported by specific providers
    }

    # Add API Base if provided (for Local AI / LM Studio)
    if api_base:
        kwargs["api_base"] = api_base

    # Add Safety Settings ONLY for Google models to avoid errors on other providers
    # (LiteLLM usually maps these, but explicit passing is safer for Vertex)
    if "vertex" in model_name or "gemini" in model_name:
        kwargs["safety_settings"] = _get_vertex_safety_settings()

    # 3. Call LLM
    try:
        response = completion(**kwargs)

        if not response.choices:
            return None

        content = response.choices[0].message.content
        return _sanitize_output(content)

    except Exception as e:
        error_msg = str(e)
        print(f"[WARNING] LLM Generation Failed: {error_msg}")
        
        # Provide helpful hints for common errors
        if "vertex" in model_name and "default credentials" in error_msg.lower():
            print("    [HINT] Run 'gcloud auth application-default login' to authenticate.")
        elif api_base and "connection" in error_msg.lower():
            print(f"    [HINT] Ensure your local LLM server is running at {api_base}")
        elif "api key" in error_msg.lower():
            print("    [HINT] Ensure your API Key environment variable is set (e.g., GEMINI_API_KEY, OPENAI_API_KEY).")
            
        return None