import ast

class CodeIssue:
    def __init__(self, node, file_path):
        self.node = node
        self.file_path = file_path
        self.start_line = node.lineno

def find_doc_issues(code: str, file_path: str):
    """Find functions and classes without docstrings."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if ast.get_docstring(node) is None:
                issues.append(CodeIssue(node, file_path))
    return issues
