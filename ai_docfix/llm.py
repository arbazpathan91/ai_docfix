from .config import get_api_key
import google.generativeai as genai

MODEL_NAME = "gemini-2.0-flash"

def generate_docstring(code_snippet: str):
    """Generate a docstring for the given code snippet using Gemini."""
    api_key = get_api_key()
    if not api_key:
        raise Exception("GOOGLE_API_KEY not set")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    
    prompt = f"""Write a clean, well-structured Python docstring for the following code.
Only output the docstring text. No backticks, no triple quotes.
Code:
{code_snippet}
"""
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.3)
    )
    
    return response.text.strip()
