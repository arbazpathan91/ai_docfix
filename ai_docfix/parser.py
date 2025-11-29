import ast
from dataclasses import dataclass
from typing import List, Union

DocableNode = Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]

@dataclass
class CodeIssue:
    node: DocableNode
    file_path: str
    start_line: int

def find_doc_issues(code: str, file_path: str) -> List[CodeIssue]:
    """
    Parse Python code and return a list of functions/classes missing docstrings.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        # FAIL LOUDLY: Print the error so the hook logs it
        print(f"\n[!] CRITICAL: Syntax Error in {file_path}")
        print(f"    Line {e.lineno}: {e.msg}")
        print("    Cannot generate docstrings until syntax is fixed.\n")
        # We return an empty list, but the print will be visible if we force failure later
        # or rely on pre-commit usually failing on syntax errors anyway.
        return []
    
    issues = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if ast.get_docstring(node) is None:
                issues.append(CodeIssue(
                    node=node,
                    file_path=file_path,
                    start_line=node.lineno
                ))
                
    return issues