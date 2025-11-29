from .config import get_api_key
import google.generativeai as genai
from typing import Optional

MODEL_NAME = "gemini-2.5-flash"

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

FILE CONTEXT (to understand the codebase):
```python
{full_file_context}
```

TARGET FUNCTION:
```python
{function_signature}
```

Generate ONLY the docstring for this specific function. 
Follow these CRITICAL rules:

1. Use Google-style docstring format
2. Keep total line length ≤ 72 characters (PEP 8)
3. Wrap long lines with proper indentation
4. Write a concise one-line summary (max 72 chars)
5. Add description only if needed (1-2 sentences, wrapped)
6. Include Args section with types and descriptions
7. Include Returns section only if function returns a value
8. Include Raises section only if function raises exceptions
9. Do NOT include Returns/Raises sections for None-returning 
   functions

FORMATTING RULES:
- Each line including indentation must be ≤ 72 characters
- Break long descriptions across multiple lines
- Indent continuation lines by 4 spaces
- Leave blank line between summary and description
- Leave blank line between description and Args

QUALITY RULES:
- Output ONLY the docstring content
- NO triple quotes (\"\"\")
- NO code blocks or markdown backticks
- NO extra formatting or explanation
- Be specific to THIS function, not similar functions
- Use clear, concise language
- Add type hints in parentheses: param (type): description
- If a function has no parameters, omit Args section
- If a function returns None or nothing, omit Returns section

EXAMPLE OUTPUT FORMAT:
One-line summary that is concise and clear.

Longer description goes here if needed. Wrap at 72
characters per line with proper indentation for
continuation lines.

Args:
    param1 (str): Description of param1 wrapped at
        72 characters if needed.
    param2 (int): Description of param2.

Returns:
    bool: Description of what is returned.

Raises:
    ValueError: When something is invalid.
"""
    
    response: genai.types.GenerateContentResponse = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3
        )
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