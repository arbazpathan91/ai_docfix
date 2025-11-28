# AI DocFix

Automatically generate docstrings for undocumented functions using Google's Gemini API.

## Installation

```bash
pip install git+https://github.com/arbazpathan91/ai_docfix.git
```

## Usage

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/arbazpathan91/ai_docfix.git
    rev: main
    hooks:
      - id: ai-docfix
        pass_env:
          - GOOGLE_API_KEY
```

Set your API key:

```bash
export GOOGLE_API_KEY="your-key-here"
```

## How it works

- Scans staged Python files for functions/classes without docstrings
- Uses Gemini to generate appropriate docstrings
- Automatically stages the changes
- You can then commit again
