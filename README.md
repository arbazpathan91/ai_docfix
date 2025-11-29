# AI DocFix

Automatically generate professional, Google-style (PEP 257) docstrings for your Python code using AI.

This tool runs as a **pre-commit hook**, detecting staged files missing docstrings and using an LLM to generate them before you commit.

## Features
- **Provider Agnostic**: Works with Google Vertex AI, OpenAI, Anthropic, or Local LLMs (Ollama/LM Studio).
- **Style Compliant**: strictly enforces Google Style formatting (Args, Returns, Raises).
- **Safety**: Uses "System Instructions" architecture to prevent safety filter false positives on technical code.
- **Smart Formatting**: Handles indentation and line-wrapping automatically.

---

## Installation

You can install the tool directly to run it manually:

```bash
pip install git+https://github.com/arbazpathan91/ai_docfix.git
```

---

## Pre-Commit Usage

Add this to your `.pre-commit-config.yaml` file. 

**Crucial**: You must add `pass_env` to allow the hook to see your API keys and configuration.

```yaml
repos:
  - repo: https://github.com/arbazpathan91/ai_docfix.git
    rev: main
    hooks:
      - id: ai-docfix
        pass_env:
          # REQUIRED: To select the model provider
          - AI_DOCFIX_MODEL

          # REQUIRED: If using Local LLMs (LM Studio/Ollama)
          - AI_DOCFIX_BASE_URL
          
          # REQUIRED: If using OpenAI or Local LLM (as dummy key)
          - OPENAI_API_KEY
          
          # REQUIRED: If using Google Vertex AI
          - GOOGLE_CLOUD_PROJECT
          - GOOGLE_APPLICATION_CREDENTIALS
          
          # REQUIRED: If using Anthropic
          - ANTHROPIC_API_KEY
```

---

## Configuration: Choose Your Provider

AI DocFix defaults to **Vertex AI**, but you can switch providers simply by setting environment variables.

### Option 1: Google Vertex AI (Default)
Best for enterprise environments. Uses `gemini-1.5-flash-002` by default.

1. Authenticate with Google Cloud:
   ```bash
   gcloud auth application-default login
   ```
2. (Optional) Set your project explicitly:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   ```

### Option 2: Local LLM (LM Studio / Ollama)
Free, privacy-focused. Runs on your machine.

1. Start your server (e.g., LM Studio) at port `1234`.
2. Configure the environment:
   ```bash
   # 'openai/' tells the tool to use the generic chat protocol
   export AI_DOCFIX_MODEL="openai/my-local-model"
   
   # Point to your local server
   export AI_DOCFIX_BASE_URL="http://localhost:1234/v1"
   
   # Required by library, but value is ignored
   export OPENAI_API_KEY="lm-studio"
   ```

### Option 3: OpenAI
Uses GPT-4o or GPT-3.5.

```bash
export AI_DOCFIX_MODEL="gpt-4o"
export OPENAI_API_KEY="sk-proj-..."
```

### Option 4: Anthropic (Claude)
Uses Claude 3.5 Sonnet or Opus.

```bash
export AI_DOCFIX_MODEL="claude-3-5-sonnet-20240620"
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Manual Usage (CLI)

You can also run the tool manually on specific files without git.

**Run on specific files:**
```bash
ai-docfix src/main.py src/utils.py
```

**Run using a specific model (overriding env vars):**
```bash
ai-docfix --model "gpt-4o" src/main.py
```

## How it works

1. **Scans**: Checks your Python files for functions/classes missing docstrings.
2. **Generates**: Sends the function signature + file context to the LLM.
3. **Validates**: Ensures the output follows PEP 257 and Google Style line wrapping (72 chars).
4. **Patches**: Inserts the docstring directly into your file.