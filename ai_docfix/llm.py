from .config import get_api_key
import google.generativeai as genai
from typing import Optional

MODEL_NAME = "gemini-flash-latest"


def generate_docstring(function_signature: str,
                       full_file_context: Optional[str] = None) -> str:
    """Generate a concise, complete docstring for the given
    function using Gemini with PEP 8 compliance."""
    api_key = get_api_key()
    if not api_key:
        raise Exception("GOOGLE_API_KEY not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    # Build context-aware prompt
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
        response: genai.types.GenerateContentResponse = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=300
            )
        )
    except Exception as e:
        raise Exception(
            f"LLM generation failed: {str(e)}"
        )

    text = response.text.strip()

    # Remove markdown code blocks if present
    if text.startswith("```python"):
        text = text[9:]  # Remove ```python
    if text.startswith("```"):
        text = text[3:]  # Remove ```

    if text.endswith("```"):
        text = text[:-3]  # Remove trailing ```

    text = text.strip()

    return text