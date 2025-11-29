"""Docstring validation and formatting utilities."""
import textwrap
import re
from typing import Tuple

def validate_line_length(docstring: str, max_length: int = 72) -> Tuple[bool, str]:
    """
    Validate that docstring lines don't exceed max length.
    
    Args:
        docstring (str): The docstring text to check.
        max_length (int): Maximum allowable line length (default 72).
        
    Returns:
        Tuple[bool, str]: (True, "") if valid, or (False, error_message).
    """
    lines = docstring.split("\n")
    violations = []
    
    for i, line in enumerate(lines, 1):
        if len(line) > max_length:
            violations.append(f"Line {i}: {len(line)} chars (max {max_length})")
    
    if violations:
        msg = "Line length violations:\n  " + "\n  ".join(violations)
        return False, msg
    
    return True, ""

def wrap_docstring(docstring: str, max_length: int = 72) -> str:
    """
    Wrap docstring lines to max length and enforce Google Style indentation.
    
    This function parses the docstring structure, detects sections (like 
    Args, Returns), and applies:
    1. 4-space indent for section bodies.
    2. 8-space hanging indent for continuation lines within sections.
    3. 0-space indent for headers and main descriptions.
    
    Args:
        docstring (str): The raw docstring from the LLM.
        max_length (int): The target line length (default 72).
        
    Returns:
        str: The fully formatted docstring.
    """
    lines = docstring.split("\n")
    wrapped_lines = []
    
    # Regex to identify standard Google Style section headers
    # Matches "Args:", "Returns:", "Raises:", etc.
    section_header_pattern = re.compile(
        r'^\s*(Args|Returns|Raises|Yields|Attributes|Example|Examples|Note|Notes)\s*:$'
    )
    
    # State tracking: Are we currently inside a structured section?
    in_section = False
    
    for line in lines:
        stripped = line.strip()
        
        # 1. Preserve empty lines (semantic separators)
        if not stripped:
            wrapped_lines.append("")
            continue
            
        # 2. Check for Section Headers
        # Headers themselves are never indented relative to the docstring block
        if section_header_pattern.match(stripped):
            in_section = True
            wrapped_lines.append(stripped)
            continue
            
        # 3. Determine Indentation Level
        # Main description (summary) = 0 spaces
        # Section body (params/returns) = 4 spaces
        base_indent = 4 if in_section else 0
        indent_str = " " * base_indent
        
        # 4. Determine Hanging Indent (for wrapping long lines)
        # Continuation lines get +4 spaces relative to base.
        # - Main desc continuation: 0 + 0 = 0 (Standard text block)
        # - Section body continuation: 4 + 4 = 8 (Hanging indent)
        #   Example:
        #       param (str): This is a long description that wraps
        #           to the next line here (8 spaces).
        if in_section:
            subsequent_indent = " " * (base_indent + 4)
        else:
            subsequent_indent = indent_str
        
        # 5. Wrap text using textwrap
        # break_long_words=False prevents breaking URLs or long variable names
        wrapped_text = textwrap.fill(
            stripped,
            width=max_length,
            initial_indent=indent_str,
            subsequent_indent=subsequent_indent,
            break_long_words=False,
            break_on_hyphens=False
        )
        
        wrapped_lines.append(wrapped_text)
    
    return "\n".join(wrapped_lines)