import re
from typing import List

def insert_docstring(original_lines: List[str], line_no: int, docstring: str) -> List[str]:
    """
    Insert a docstring after a function or class definition.

    Args:
        original_lines (List[str]): List of all file lines.
        line_no (int): Line number of def/class statement (0-indexed).
        docstring (str): The clean docstring to insert.

    Returns:
        List[str]: Modified lines with docstring inserted.
    """
    # Defensive check
    if line_no < 0 or line_no >= len(original_lines):
        return original_lines

    def_line = original_lines[line_no]

    # Robust indentation extraction (handles spaces or tabs)
    # We grab whatever whitespace exists at the start of the definition line.
    match = re.match(r"^\s*", def_line)
    base_indent = match.group(0) if match else ""
    
    # Standard Python indentation is 4 spaces deeper than the definition
    # We assume standard 4-space indentation for the body.
    body_indent = base_indent + "    "

    # Clean quotes to ensure we don't double-wrap
    docstring = docstring.strip()
    if docstring.startswith('"""'): 
        docstring = docstring[3:]
    if docstring.endswith('"""'): 
        docstring = docstring[:-3]
    docstring = docstring.strip()

    doc_lines = docstring.split("\n")

    # Build the final docstring block
    formatted_lines = []
    formatted_lines.append(f'{body_indent}"""')

    for line in doc_lines:
        if not line:
            formatted_lines.append("")
        else:
            # We apply the global body indentation to every line.
            # Relative indentation (like for Args/Returns) is preserved 
            # because 'line' comes from validator.py which handles that.
            formatted_lines.append(f'{body_indent}{line}')

    formatted_lines.append(f'{body_indent}"""')
    # Add a blank line to separate docstring from code body
    formatted_lines.append("") 

    return (
        original_lines[:line_no + 1] +
        formatted_lines +
        original_lines[line_no + 1:]
    )