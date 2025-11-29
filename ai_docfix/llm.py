from .config import get_api_key
import google.generativeai as genai

MODEL_NAME = "gemini-2.5-flash"


def generate_docstring(function_signature: str,
                       full_file_context: str = None):
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

TARGET FUNCTION TO DOCUMENT:
The function/class marked between the === markers below is
the ONLY one you should write a docstring for. Ignore any
similar functions in the file context above.

{function_signature}

Generate ONLY the docstring for the function/class marked
above between the === markers. Do NOT use docstrings from
other functions.

Follow these CRITICAL rules:

1. Use Google-style docstring format
2. Keep total line length ≤ 72 characters (PEP 8)
3. Wrap long lines with proper indentation
4. Write a concise one-line summary (max 72 chars)
5. Add description only if needed (1-2 sentences, wrapped)
6. Include Args section with types and descriptions
7. Include Returns section only if function returns a value
8. Include Raises section only if function raises exceptions
9. Do NOT include Returns/Raises for None-returning functions

FORMATTING RULES:
- Each line including indentation must be ≤ 72 characters
- Break long descriptions across multiple lines
- Indent continuation lines by 8 spaces total (4 for body + 4)
- Leave blank line between summary and description
- Leave blank line between description and Args
- In Args/Returns: description starts after type on same line
- If description is long, wrap to next line with 8-space indent

EXAMPLE:
    Args:
        param1 (str): Short description.
        param2 (dict): This is a longer description that
            wraps to the next line with extra indent.
    
    Returns:
        bool: This is a long return description that
            wraps properly to the next line.

QUALITY RULES:
- Output ONLY the docstring content
- NO triple quotes ("\"\"\)
- NO code blocks or markdown backticks
- NO extra formatting or explanation
- Be specific to THIS function only
- Use clear, concise language
- Add type hints: param (type): description
- If no parameters, omit Args section
- If returns None, omit Returns section
- Do NOT duplicate the docstring
- Ensure consistent indentation throughout
- For __init__ methods: only include Args for parameters
  passed to __init__, not attributes set internally
"""

    response = model.generate_content(
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