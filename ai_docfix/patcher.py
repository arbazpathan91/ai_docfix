def insert_docstring(original_lines, line_no, docstring):
    """Insert docstring after the function/class definition with proper formatting."""
    # Get indentation from the function/class definition line
    def_line = original_lines[line_no]
    indent = " " * (len(def_line) - len(def_line.lstrip()))
    
    # Add extra indentation for docstring body
    body_indent = indent + "    "
    
    # Clean up docstring
    docstring = docstring.strip()
    
    # Remove existing triple quotes if present
    if docstring.startswith('"""'):
        docstring = docstring[3:]
    if docstring.endswith('"""'):
        docstring = docstring[:-3]
    
    docstring = docstring.strip()
    
    # Split into lines
    doc_lines = docstring.split("\n")
    
    # Format the docstring properly
    formatted_lines = []
    formatted_lines.append(f'{body_indent}"""')
    
    for line in doc_lines:
        # Add indentation to each line
        if line.strip():  # Non-empty line
            formatted_lines.append(f'{body_indent}{line}')
        else:  # Empty line
            formatted_lines.append("")
    
    formatted_lines.append(f'{body_indent}"""')
    formatted_lines.append("")  # Blank line after docstring
    
    # Insert after the function/class definition
    return (
        original_lines[:line_no + 1] +
        formatted_lines +
        original_lines[line_no + 1:]
    )