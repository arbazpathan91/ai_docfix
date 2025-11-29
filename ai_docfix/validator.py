"""Docstring validation utilities."""

def validate_line_length(docstring: str, max_length: int = 72):
    """Validate that docstring lines don't exceed max length.
    
    Args:
        docstring (str): The docstring to validate.
        max_length (int): Maximum line length allowed.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    lines = docstring.split("\n")
    violations = []
    
    for i, line in enumerate(lines, 1):
        if len(line) > max_length:
            violations.append(
                f"Line {i}: {len(line)} chars (max {max_length})"
            )
    
    if violations:
        msg = "Line length violations:\n  " + "\n  ".join(
            violations
        )
        return False, msg
    
    return True, ""

def wrap_docstring(docstring: str, max_length: int = 72):
    """Wrap docstring lines to max length with proper indentation.
    
    Args:
        docstring (str): The docstring to wrap.
        max_length (int): Maximum line length.
    
    Returns:
        str: The wrapped docstring.
    """
    lines = docstring.split("\n")
    wrapped_lines = []
    
    for line in lines:
        if len(line) <= max_length:
            wrapped_lines.append(line)
            continue
        
        # Get base indentation
        indent = len(line) - len(line.lstrip())
        indent_str = " " * indent
        
        # For continuation lines in Args/Returns, add extra indent
        if line.lstrip().startswith(('Args:', 'Returns:', 
                                      'Raises:', 'Yields:')):
            wrapped_lines.append(line)
        elif indent > 0 and ':' in line:
            # This is a parameter line - preserve it
            wrapped_lines.append(line)
        else:
            # Wrap long description lines
            words = line.split()
            current_line = indent_str + words[0]
            
            for word in words[1:]:
                test_line = current_line + " " + word
                if len(test_line) <= max_length:
                    current_line = test_line
                else:
                    wrapped_lines.append(current_line)
                    # Continuation lines get extra indent
                    continuation_indent = " " * (indent + 4)
                    current_line = continuation_indent + word
            
            wrapped_lines.append(current_line)
    
    return "\n".join(wrapped_lines)