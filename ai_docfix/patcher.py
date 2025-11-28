def insert_docstring(original_lines, line_no, docstring):
    """Insert docstring after the function/class definition."""
    indent = " " * (len(original_lines[line_no]) - len(original_lines[line_no].lstrip()))
    
    docstring = docstring.strip()
    
    if docstring.startswith('"""') and docstring.endswith('"""'):
        docstring = docstring[3:-3].strip()
    elif docstring.startswith("'''") and docstring.endswith("'''"):
        docstring = docstring[3:-3].strip()
    
    docstring_lines = docstring.split("\n")
    
    if len(docstring_lines) == 1:
        doc_lines = [f'{indent}"""{docstring_lines[0]}"""', ""]
    else:
        doc_lines = [f'{indent}"""']
        for line in docstring_lines:
            doc_lines.append(f'{indent}{line}')
        doc_lines.append(f'{indent}"""')
        doc_lines.append("")
    
    return (
        original_lines[:line_no + 1] +
        doc_lines +
        original_lines[line_no + 1:]
    )
