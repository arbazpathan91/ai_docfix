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

# Updated Prompt to prevent context leakage
SYSTEM_INSTRUCTION = """
You are a Senior Python Technical Writer. 
Your only task is to write Google-style (PEP 257) docstrings for Python code.

RULES:
1. Describe *what* the code does and *why*, not *how*.
2. Use sections: Args, Returns, Raises (if applicable).
3. Do NOT output markdown ticks (```).
4. Do NOT output the enclosing triple quotes. Return ONLY the docstring text.
5. If arguments or returns are None, omit those sections.
6. FOCUS: Document ONLY the specific function/class signature provided in the 'TARGET CODE' block. Do NOT document subsequent functions or classes found in the file context.
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
EXAMPLE INPUT:
def add(a, b): return a + b
EXAMPLE OUTPUT:
Add two numbers.

Args:
    a (int): First number.
    b (int): Second number.

Returns:
    int: The sum.

TARGET CODE TO DOCUMENT (Focus only on this):
{function_signature}
"""
    
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user_prompt}
    ]

    kwargs = {
        "model": model_name,
        "messages": messages,
        "temperature": gen_config["temperature"],
        "max_tokens": gen_config["max_tokens"],
        "stop": ['"""'],
        "drop_params": True,
    }

    if api_base: kwargs["api_base"] = api_base
    if "vertex" in model_name or "gemini" in model_name:
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