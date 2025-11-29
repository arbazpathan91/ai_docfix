from .config import get_api_key
import google.generativeai as genai

MODEL_NAME = "gemini-2.0-flash"

def generate_docstring(code_snippet: str, full_file_context: str = None):
    """Generate a concise, complete docstring for the given code snippet using Gemini."""
    api_key = get_api_key()
    if not api_key:
        raise Exception("GOOGLE_API_KEY not set")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Build context-aware prompt
    if full_file_context:
        prompt = f"""You are a Python documentation expert. Analyze the entire file context first to understand the module's purpose and patterns, then generate a concise but complete docstring for the function/class.

FILE CONTEXT:
```python
{full_file_context}
```

TARGET CODE:
```python
{code_snippet}
```

Generate a concise docstring that includes:
- Brief one-line summary
- Longer description if needed (2-3 sentences max)
- Args section with types and descriptions
- Returns section with type and description
- Raises section if applicable

Requirements:
- Be concise but complete
- Use proper Python docstring format (Google style)
- Only output the docstring text, no triple quotes
- No code blocks or markdown
- Match the file's patterns and conventions
"""
    else:
        prompt = f"""Generate a concise but complete Python docstring for this function/class.

CODE:
```python
{code_snippet}
```

Generate a docstring that includes:
- Brief one-line summary
- Longer description if needed (2-3 sentences max)
- Args section with types and descriptions
- Returns section with type and description
- Raises section if applicable

Requirements:
- Be concise but complete
- Use proper Python docstring format (Google style)
- Only output the docstring text, no triple quotes
- No code blocks or markdown
"""
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.3)
    )
    
    return response.text.strip()