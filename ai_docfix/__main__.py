import sys
import os
import argparse
from .hook import main

def cli():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description="AI DocFix - Auto-generate docstrings using LiteLLM"
    )
    
    parser.add_argument(
        '--model', 
        type=str, 
        help='Override the AI model (e.g., "vertex_ai/gemini-1.5-flash", "gpt-4o")'
    )
    
    parser.add_argument(
        'files', 
        nargs='*', 
        help='Specific files to process (if empty, defaults to git staged files)'
    )
    
    args = parser.parse_args()
    
    # Set the model override in environment so llm.py picks it up globally
    if args.model:
        os.environ["AI_DOCFIX_MODEL"] = args.model
    
    # Pass specific files list to the main hook logic
    sys.exit(main(files=args.files))

if __name__ == "__main__":
    cli()