from .config import get_api_key
import google.generativeai as genai

MODEL_NAME = "gemini-2.0-flash"


def generate_docstring(function_signature: str,
                       full_file_context: str = None):
    """Generate a docstring for the given function."""
    api_key = get_api_key()
    if not api_key:
        raise Exception("GOOGLE_API_KEY not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""Write a Python docstring for this function.

Function:
{function_signature}

Requirements:
- Use Google-style format
- Keep lines under 72 characters
- Include Args, Returns, Raises if applicable
- Be concise and clear
- Output only the docstring text, no quotes or code blocks
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=200,
                top_p=0.8
            )
        )

        if not response.text:
            raise Exception(
                "LLM returned empty response. "
                "Try again or check your API quota."
            )

        text = response.text.strip()

    except Exception as e:
        raise Exception(
            f"LLM generation failed: {str(e)}"
        )

    # Remove markdown code blocks if present
    if text.startswith("```python"):
        text = text[9:]
    if text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    return text