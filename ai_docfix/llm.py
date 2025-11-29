import google.generativeai as genai
from typing import Optional
from .config import get_api_key

# gemini-1.5-flash is optimized for high-volume tasks like this
MODEL_NAME = "gemini-flash-latest"

def generate_docstring(function_signature: str,
                       full_file_context: Optional[str] = None) -> Optional[str]:
    """
    Generate a concise, PEP 257 compliant docstring for the given code.

    This function communicates with the Gemini API to generate documentation.
    It handles safety settings to prevent false positives on code keywords
    (like 'delete' or 'exec') and uses full file context for accurate type inference.

    Args:
        function_signature: The specific function or class definition to document.
        full_file_context: The entire source code of the file (for context).

    Returns:
        The generated docstring text (cleaned of quotes), or None if generation failed.
    """
    api_key = get_api_key()
    if not api_key:
        print("[WARNING] GOOGLE_API_KEY not set, skipping docstring generation")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    # -------------------------------------------------------------------------
    # SAFETY SETTINGS
    # We explicitly allow "Dangerous Content" because source code often contains
    # words like 'kill', 'execute', 'payload', or 'delete' which trigger
    # standard AI safety filters.
    # -------------------------------------------------------------------------
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # -------------------------------------------------------------------------
    # PROMPT CONSTRUCTION
    # -------------------------------------------------------------------------
    context_block = ""
    if full_file_context:
        context_block = f"""
CONTEXT (Full File Content):
The following is the full source code. Use this to understand custom types 
(e.g., if a function returns 'StoreData', look here to see what that is).
```python
{full_file_context}
```
"""

    prompt = f"""You are a Python documentation expert analyzing safe, educational code.
Generate a PEP 257 Google-style docstring for the specific code element below.

{context_block}

TARGET ELEMENT TO DOCUMENT:
============================================================
{function_signature}
============================================================

INSTRUCTIONS:
1. **Context Awareness**: Use the provided 'Full File Content' to infer types and logic.
2. **Classes**: If the target is a CLASS, describe what the object represents. Do NOT document `__init__` arguments here.
3. **Methods**: If the target is a FUNCTION/METHOD, describe its logic, args, and returns.
4. **Format**: Google-style (`Args:`, `Returns:`, `Raises:`).
5. **Conciseness**: Keep descriptions brief and professional.

OUTPUT RULES:
- Output ONLY the raw docstring text.
- NO triple quotes ("\"\"\).
- NO markdown fencing (```).
- NO conversational filler ("Here is the docstring...").
"""

    # -------------------------------------------------------------------------
    # GENERATION
    # -------------------------------------------------------------------------
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low temp = more factual/deterministic
                max_output_tokens=500
            ),
            safety_settings=safety_settings
        )

        # Validate Response
        if not response.candidates:
            # Check prompt feedback to see if it was blocked before generation
            print(f"[WARNING] API response blocked. Feedback: {response.prompt_feedback}")
            return None

        candidate = response.candidates[0]

        # Check for safety blocks or other stop reasons
        # 1 = STOP (Success), 3 = MAX_TOKENS, 4 = RECITATION
        if candidate.finish_reason not in [1, 3]: 
            print(f"[WARNING] Generation stopped abnormally (finish_reason: {candidate.finish_reason})")
            return None

        if not candidate.content or not candidate.content.parts:
            print("[WARNING] No content parts in response")
            return None

        text = candidate.content.parts[0].text.strip()

    except Exception as e:
        print(f"[WARNING] LLM generation failed: {str(e)}")
        return None

    # -------------------------------------------------------------------------
    # POST-PROCESSING
    # -------------------------------------------------------------------------
    clean_lines = []
    for line in text.split('\n'):
        line = line.strip()
        # Remove markdown code blocks if the LLM hallucinated them
        if line.startswith("```"):
            continue
        # Remove literal triple quotes if the LLM disobeyed instructions
        if line.startswith('"""'):
            line = line.replace('"""', '')
        if line.endswith('"""'):
            line = line.replace('"""', '')
        
        # Don't add empty lines at the very start
        if not clean_lines and not line:
            continue
            
        clean_lines.append(line)

    final_text = "\n".join(clean_lines).strip()

    # Final sanity check on length
    if len(final_text) < 10:
        return None

    return final_text