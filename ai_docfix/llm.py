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
# STRICT SYSTEM INSTRUCTIONS
# =============================================================================
SYSTEM_INSTRUCTION = """
You are a strict Python Documentation Engine.
Generate a Google-style docstring ONLY for the specific code provided in the <TARGET> tag.

CRITICAL RULES:
1. **Scope**: Document ONLY the function/class signature found inside <TARGET>. Ignore any other code in <CONTEXT>.
2. **Stop**: Do NOT describe subsequent functions, methods, or classes. One docstring per request.
3. **Self**: Do NOT document the 'self' or 'cls' arguments.
4. **Classes**: Use 'Attributes' for class variables. Do NOT use 'Args' in class docstrings (put those in __init__).
5. **Format**: Return raw docstring text only. No markdown formatting (no ```python).
6. **Brevity**: Be concise. Describe WHAT and WHY, not HOW.
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

    # We wrap the context in XML tags to help the LLM distinguish boundaries
    context_block = ""
    if full_file_context:
        context_block = f"""
<CONTEXT_FILE>
(Use this ONLY for type reference. DO NOT document this code.)
{full_file_context}
</CONTEXT_FILE>
"""

    user_prompt = f"""{context_block}

<TARGET_TO_DOCUMENT>
{function_signature}
</TARGET_TO_DOCUMENT>

Generate the docstring for the code inside <TARGET_TO_DOCUMENT> only.
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
        "stop": ['"""', "<TARGET>", "</TARGET>"], # Extra stop tokens
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