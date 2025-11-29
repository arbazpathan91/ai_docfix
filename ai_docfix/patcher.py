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

    # Calculate indentation
    indent_count = 0
    for char in def_line:
        if char == ' ':
            indent_count += 1
        else:
            break

    body_indent = " " * (indent_count + 4)

    # Clean docstring - remove triple quotes if present
    docstring = docstring.strip()

    if docstring.startswith('"""'):
        docstring = docstring[3:]
    if docstring.endswith('"""'):
        docstring = docstring[:-3]

    docstring = docstring.strip()

    # Split into lines
    doc_lines = docstring.split("\n")

    # Format with proper indentation
    formatted_lines = []
    formatted_lines.append(f'{body_indent}"""')

    for line in doc_lines:
        stripped = line.strip()

        # Preserve structure: Args:, Returns:, etc stay left
        # but content gets indented
        if stripped.endswith(':') and stripped in [
            'Args', 'Returns', 'Raises', 'Yields', 'Note',
            'Notes', 'Example', 'Examples', 'Attributes'
        ]:
            formatted_lines.append(f'{body_indent}{stripped}')
        elif stripped and not stripped[0].isupper():
            # Parameter line or description - add extra indent
            if ':' in stripped:
                # Parameter with description
                formatted_lines.append(
                    f'{body_indent}    {stripped}'
                )
            else:
                # Regular line
                formatted_lines.append(f'{body_indent}{stripped}')
        elif stripped:
            # Regular content line
            formatted_lines.append(f'{body_indent}{stripped}')
        else:
            # Blank line
            formatted_lines.append("")

    formatted_lines.append(f'{body_indent}"""')
    formatted_lines.append("")

    return (
        original_lines[:line_no + 1] +
        formatted_lines +
        original_lines[line_no + 1:]
    )