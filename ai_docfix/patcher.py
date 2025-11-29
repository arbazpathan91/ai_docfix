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
    indent = " " * (len(def_line) - len(def_line.lstrip()))
    body_indent = indent + "    "

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
        if line.strip():
            formatted_lines.append(f'{body_indent}{line}')
        else:
            formatted_lines.append("")

    formatted_lines.append(f'{body_indent}"""')
    formatted_lines.append("")

    return (
        original_lines[:line_no + 1] +
        formatted_lines +
        original_lines[line_no + 1:]
    )