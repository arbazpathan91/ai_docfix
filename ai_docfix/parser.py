import ast
from dataclasses import dataclass
from typing import List, Union

# Define the types of nodes we care about
DocableNode = Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]

@dataclass
class CodeIssue:
    """Represents a code node (function/class) missing a docstring."""
    node: DocableNode
    file_path: str
    start_line: int

def find_doc_issues(code: str, file_path: str) -> List[CodeIssue]:
    """
    Parse Python code and return a list of functions/classes missing docstrings.
    
    Args:
        code (str): The raw source code of the file.
        file_path (str): The path to the file (for reporting purposes).
        
    Returns:
        List[CodeIssue]: A list of detected issues.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"[WARNING] Syntax error in {file_path}: {e}")
        return []
    
    issues = []
    
    for node in ast.walk(tree):
        # Check if it's a function (sync/async) or class
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Check if it lacks a docstring
            if ast.get_docstring(node) is None:
                # Note: node.lineno is 1-indexed
                issues.append(CodeIssue(
                    node=node,
                    file_path=file_path,
                    start_line=node.lineno
                ))
                
    return issues