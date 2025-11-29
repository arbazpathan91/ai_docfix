from .config import get_api_key
import google.generativeai as genai
from typing import Optional

MODEL_NAME = "gemini-2.0-flash"

def generate_docstring(function_signature: str, full_file_context: Optional[str] = None) -> str:
    """Generate a concise, complete docstring for the given function using Gemini."""
    api_key = get_api_key()
    if not api_key:
        raise Exception("GOOGLE_API_KEY not set")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Build context-aware prompt
    prompt = f"""
You are a Python documentation expert. Your task is to generate a docstring for a specific function.

FILE CONTEXT (to understand the codebase):
```python
{full_file_context}
```

TARGET FUNCTION:
```python
{function_signature}
```

Generate ONLY the docstring for this specific function. Follow these rules:

1. Write a concise one-line summary
2. Add a longer description if needed (max 2-3 sentences)
3. Include Args section with parameter names, types, and descriptions
4. Include Returns section with type and description
5. Include Raises section only if the function raises exceptions
6. Use Google-style docstring format

CRITICAL RULES:
- Output ONLY the docstring content
- NO triple quotes (\"\"\")
- NO code blocks or markdown backticks
- NO extra formatting or explanation
- Be specific to THIS function, not similar functions
- Keep it concise but complete
- If a function has no parameters, do NOT include an Args section
- If a function doesn't return anything, do NOT include a Returns section
"""
    
    response: genai.types.GenerateContentResponse = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.3)
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