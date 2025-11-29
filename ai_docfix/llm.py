from .config import get_api_key
import google.generativeai as genai
from typing import Optional

MODEL_NAME = "gemini-3-pro-preview"


def generate_docstring(function_signature: str,
                       full_file_context: Optional[str] = None) -> Optional[str]:
    """Generate a concise, complete docstring for the given function.
    
    Uses Gemini with PEP 8 compliance. Returns None if generation fails
    (e.g., due to safety filters or API errors) to allow hook to continue.
    
    Args:
        function_signature: The function signature to document
        full_file_context: Optional full file content for context
        
    Returns:
        Generated docstring text without triple quotes, or None if failed
    """
    api_key = get_api_key()
    if not api_key:
        print("[WARNING] GOOGLE_API_KEY not set, skipping docstring generation")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""You are a Python documentation expert.
Generate a PEP 257 compliant docstring for a specific function.

TARGET FUNCTION TO DOCUMENT:
The function/class marked between the === markers below is
the ONLY one you should write a docstring for.

{function_signature}

Generate ONLY the docstring for the marked function above.
Do NOT use docstrings from other functions.

Follow these rules:

1. Google-style docstring format
2. Line length ≤ 72 characters (PEP 8)
3. Concise one-line summary
4. Brief description (1-2 sentences if needed)
5. Args section with types and descriptions
6. Returns section only if function returns a value
7. Raises section only if function raises exceptions
8. Do NOT include Returns/Raises for None-returning functions

OUTPUT RULES:
- Output ONLY the docstring content
- NO triple quotes (\"\"\")
- NO code blocks or markdown
- NO extra text or explanation
- Be specific to THIS function only
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=300
            )
            # Using default safety settings - no safety_settings parameter
        )
        
        # Check if response was blocked
        if not response.candidates:
            print("[WARNING] API response blocked: No candidates returned")
            return None
        
        candidate = response.candidates[0]
        
        # Check finish reason
        if candidate.finish_reason == 2:  # SAFETY
            print("[WARNING] Response blocked by safety filters, skipping this function")
            return None
        
        if candidate.finish_reason not in [0, 1]:  # UNSPECIFIED or STOP
            print(f"[WARNING] Generation incomplete (finish_reason: {candidate.finish_reason})")
            return None
        
        # Check for content
        if not candidate.content or not candidate.content.parts:
            print("[WARNING] No content parts in response")
            return None
            
        text = candidate.content.parts[0].text.strip()
        
    except Exception as e:
        print(f"[WARNING] LLM generation failed: {str(e)}")
        return None

    # Remove markdown code blocks if present
    if text.startswith("```python"):
        text = text[9:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()
    
    # Final validation - ensure we got something useful
    if not text or len(text) < 10:
        print("[WARNING] Generated docstring too short or empty")
        return None
    
    return text