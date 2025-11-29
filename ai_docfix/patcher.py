"""Insert docstrings into Python files."""


def insert_docstring(original_lines, line_no, docstring):
    """Insert a docstring after a function or class definition.

    Args:
        original_lines (list): List of all file lines.
        line_no (int): Line number of def/class statement.
        docstring (str): The docstring to insert.

    Returns:
        list: Modified lines with docstring inserted.
    """
    def_line = original_lines[line_no]

    indent_count = 0
    for char in def_line:
        if char == ' ':
            indent_count += 1
        else:
            break

    body_indent = " " * (indent_count + 4)

    docstring = docstring.strip()

    if docstring.startswith('"""'):
        docstring = docstring[3:]
    if docstring.endswith('"""'):
        docstring = docstring[:-3]

    docstring = docstring.strip()

    doc_lines = docstring.split("\n")

    formatted_lines = []
    formatted_lines.append(f'{body_indent}"""')

    for line in doc_lines:
        stripped = line.strip()

        if stripped.endswith(':') and stripped in [
            'Args', 'Returns', 'Raises', 'Yields', 'Note',
            'Notes', 'Example', 'Examples', 'Attributes'
        ]:
            formatted_lines.append(f'{body_indent}{stripped}')
        elif stripped and not stripped[0].isupper():
            if ':' in stripped:
                formatted_lines.append(
                    f'{body_indent}    {stripped}'
                )
            else:
                formatted_lines.append(f'{body_indent}{stripped}')
        elif stripped:
            formatted_lines.append(f'{body_indent}{stripped}')
        else:
            formatted_lines.append("")

    formatted_lines.append(f'{body_indent}"""')
    formatted_lines.append("")

    return (
        original_lines[:line_no + 1] +
        formatted_lines +
        original_lines[line_no + 1:]
    )