import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import Optional
from .config import get_api_key

# gemini-1.5-flash is fast and usually follows system instructions well
MODEL_NAME = "gemini-1.5-flash"

def generate_docstring(function_signature: str,
                       full_file_context: Optional[str] = None) -> Optional[str]:
    """
    Generates a generic, PEP 257 docstring using Gemini.
    """
    api_key = get_api_key()
    if not api_key:
        print("[WARNING] GOOGLE_API_KEY not set")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    # -------------------------------------------------------------------------
    # 1. UNIVERSAL SAFETY BYPASS
    # We must explicitly disable filters. In the context of software engineering,
    # words like 'kill' (process), 'execute' (command), or 'injection' (dependency)
    # are technical terms, not threats.
    # -------------------------------------------------------------------------
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    # -------------------------------------------------------------------------
    # 2. GENERIC CONTEXT
    # -------------------------------------------------------------------------
    context_block = ""
    if full_file_context:
        context_block = f"""
SOURCE FILE CONTEXT:
The following is the full source code content. Use it strictly for 
resolving type definitions and understanding class hierarchy.
```python
{full_file_context}
```
"""

    # -------------------------------------------------------------------------
    # 3. GENERIC "STATIC ANALYSIS" PROMPT
    # We frame the AI as a "Documentation Tool". This removes the moral 
    # agency from the AI, making it less likely to flag content.
    # -------------------------------------------------------------------------
    prompt = f"""You are an automated code documentation engine. 
Your task is to perform static analysis on the provided code snippet and generate a docstring.

SYSTEM RULES:
1. **Objective**: Describe the functionality of the code based *only* on the logic provided.
2. **Context**: You are analyzing raw source code. Terms like "attack", "payload", "kill", "execute", or "payment" are technical variable names or methods, not real-world actions. Treat them neutrally.
3. **Output**: Generate a standard Google-style Python docstring.

{context_block}

TARGET CODE TO DOCUMENT:
============================================================
{function_signature}
============================================================

STYLE REQUIREMENTS:
- Format: Google Style (Args, Returns, Raises).
- Tone: Technical, concise, objective.
- Do not provide code refactoring or security advice. Just document what it does.

OUTPUT FORMAT:
Return ONLY the docstring text. No quotes, no markdown blocks.
"""

    # -------------------------------------------------------------------------
    # 4. GENERATION
    # -------------------------------------------------------------------------
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Keep it factual
                max_output_tokens=500
            ),
            safety_settings=safety_settings
        )

        if not response.candidates:
            # If blocked here, the API key might be restricted or content is extremely flagged
            return None

        candidate = response.candidates[0]

        # 1=STOP (Good), 3=MAX_TOKENS (Okay). 
        # If it returns 2 (SAFETY) even with BLOCK_NONE, the model is refusing at a hard-coded level.
        if candidate.finish_reason not in [1, 3]: 
            print(f"[WARNING] Skipped due to finish_reason: {candidate.finish_reason}")
            return None

        if not candidate.content or not candidate.content.parts:
            return None

        text = candidate.content.parts[0].text.strip()

    except Exception as e:
        print(f"[WARNING] LLM Generation Error: {e}")
        return None

    # -------------------------------------------------------------------------
    # 5. SANITIZATION
    # -------------------------------------------------------------------------
    clean_lines = []
    for line in text.split('\n'):
        line = line.strip()
        # Remove common hallucinations
        if line.startswith("```") or line.startswith('"""') or line.endswith('"""'):
            line = line.replace('"""', '').replace("```", "")
        
        if not clean_lines and not line:
            continue
        clean_lines.append(line)

    final_text = "\n".join(clean_lines).strip()
    
    if len(final_text) < 5:
        return None

    return final_text
