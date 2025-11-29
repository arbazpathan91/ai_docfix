import os
import sys
from typing import Optional, List, Dict, Any

try:
    import litellm
    from litellm import completion
    from litellm.exceptions import APIConnectionError, RateLimitError, ServiceUnavailableError
except ImportError:
    print("[ERROR] 'litellm' is not installed. Please run: pip install litellm")
    sys.exit(1)

from .config import get_model_name, get_api_base, get_generation_config

# =============================================================================
# REFINED SYSTEM INSTRUCTIONS
# =============================================================================
SYSTEM_INSTRUCTION = """
You are a Senior Python Technical Writer. 
Your only task is to write Google-style (PEP 257) docstrings for Python code.

RULES:
1. **Completeness**: Write full, grammatical sentences. Do not leave sentences unfinished.
2. **Structure**: 
   - Use `Args`, `Returns`, `Raises` for functions.
   - Use `Attributes` for Classes (do NOT use `Args` in class docstrings).
3. **Format**: Return ONLY the docstring text. No markdown (```), no enclosing triple quotes.
4. **Focus**: Document ONLY the code provided in <TARGET_TO_DOCUMENT>. Do not hallucinate or document subsequent code.
5. **Self**: Do NOT document the 'self' argument.
"""

def _get_vertex_safety_settings() -> List[Dict[str, str]]:
    return [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

def _sanitize_output(text: str) -> Optional[str]:
    if not text: return None
    clean_lines = []
    lines = text.split('\n')
    for line in lines:
        line = line.rstrip()
        if line.strip().startswith("```"): continue
        if line.strip() in ['"""', "'''"]: continue
        clean_lines.append(line)
    
    # Ensure the last line is not just a trailing quote
    if clean_lines and clean_lines[-1].strip() in ['"""', "'''"]:
        clean_lines.pop()

    while clean_lines and not clean_lines[0].strip(): clean_lines.pop(0)
    while clean_lines and not clean_lines[-1].strip(): clean_lines.pop()
    
    return "\n".join(clean_lines)

def generate_docstring(function_signature: str,
                       full_file_context: Optional[str] = None) -> Optional[str]:
    
    model_name = get_model_name()
    api_base = get_api_base()
    gen_config = get_generation_config()

    if "vertex_ai" in model_name or "gemini" in model_name:
        api_base = None

    context_str = f"CONTEXT FILE:\n{full_file_context}\n\n" if full_file_context else ""
    
    user_prompt = f"""{context_str}
EXAMPLE FUNCTION:
def add(a, b): return a + b
DOCSTRING:
Add two numbers.

Args:
    a (int): First number.
    b (int): Second number.

Returns:
    int: The sum.

<TARGET_TO_DOCUMENT>
{function_signature}
</TARGET_TO_DOCUMENT>

Generate the docstring for the code inside <TARGET_TO_DOCUMENT>.
"""
    
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user_prompt}
    ]

    kwargs = {
        "model": model_name,
        "messages": messages,
        "temperature": gen_config["temperature"],
        # Increase tokens slightly to prevent mid-sentence cutoff
        "max_tokens": 1024, 
        "stop": ['"""', "<TARGET>"], 
        "drop_params": True,
    }

    if api_base: kwargs["api_base"] = api_base
    if "vertex_ai" in model_name or "gemini" in model_name:
        kwargs["safety_settings"] = _get_vertex_safety_settings()

    try:
        response = completion(**kwargs)
        if not response.choices: return None
        content = response.choices[0].message.content
        return _sanitize_output(content)
    except Exception as e:
        error_msg = str(e)
        print(f"[WARNING] LLM Generation Failed: {error_msg}")
        return None