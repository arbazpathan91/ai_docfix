"""Docstring insertion utilities."""


def insert_docstring(original_lines, line_no, docstring):
    """Insert docstring after function/class definition.

    Args:
        original_lines (list): List of file lines.
        line_no (int): Line number of the definition.
        docstring (str): The docstring to insert.

    Returns:
        list: Modified list with docstring inserted.
    """
    def_line = original_lines[line_no]
    
    # Calculate indentation - count spaces before first non-space
    indent_count = 0
    for char in def_line:
        if char == ' ':
            indent_count += 1
        else:
            break
    
    indent = " " * indent_count
    body_indent = " " * (indent_count + 4)

    # Clean docstring
    docstring = docstring.strip()

    # Remove triple quotes if LLM added them
    if docstring.startswith('"""'):
        docstring = docstring[3:]
    if docstring.endswith('"""'):
        docstring = docstring[:-3]

    docstring = docstring.strip()

    # Split into lines and format consistently
    doc_lines = docstring.split("\n")

    formatted_lines = []
    formatted_lines.append(f'{body_indent}"""')

    for line in doc_lines:
        stripped = line.strip()
        if stripped:
            # Remove any leading spaces and re-add consistent indent
            formatted_lines.append(f'{body_indent}{stripped}')
        else:
            # Preserve blank lines
            formatted_lines.append("")

    formatted_lines.append(f'{body_indent}"""')
    formatted_lines.append("")

    return (
        original_lines[:line_no + 1] +
        formatted_lines +
        original_lines[line_no + 1:]
    )