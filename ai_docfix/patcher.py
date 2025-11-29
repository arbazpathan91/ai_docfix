import subprocess
import sys
import ast
from .parser import find_doc_issues
from .llm import generate_docstring
from .patcher import insert_docstring
from .validator import validate_line_length, wrap_docstring

def get_staged_files():
    """Get staged Python files from git."""
    try:
        output = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"]
        ).decode().strip()
        if not output:
            return []
        return [f for f in output.split("\n") if f.endswith(".py")]
    except subprocess.CalledProcessError:
        return []

def extract_function_signature(lines, line_no):
    """Extract just the function/class definition and a few lines of body."""
    # Find the start of the def/class line
    start = line_no
    
    # Collect the definition line(s) - might span multiple lines
    sig_lines = [lines[start]]
    i = start + 1
    
    # For multi-line signatures (with \ or unclosed parens), keep collecting
    while i < len(lines) and (
        lines[i].strip().startswith("->") or 
        lines[i].strip().startswith(")") or
        "(" in lines[start] and ")" not in "\n".join(sig_lines)
    ):
        sig_lines.append(lines[i])
        i += 1
    
    # Add a few lines of body for context
    for j in range(i, min(i + 5, len(lines))):
        sig_lines.append(lines[j])
    
    return "\n".join(sig_lines)

def process_file(path):
    """Process a single file to add missing docstrings."""
    try:
        with open(path, "r", encoding="utf8") as f:
            original = f.read()
    except Exception as e:
        print(f"[ERROR] Could not read {path}: {e}")
        return False
    
    lines = original.split("\n")
    issues = find_doc_issues(original, path)
    
    if not issues:
        return False
    
    # Sort issues in reverse order to avoid line number shifting
    issues.sort(key=lambda x: x.start_line, reverse=True)
    
    for issue in issues:
        try:
            # Extract just the function signature
            func_signature = extract_function_signature(
                lines, issue.start_line - 1
            )
            
            # Generate docstring
            doc = generate_docstring(
                function_signature=func_signature,
                full_file_context=original
            )
            
            # Validate and wrap docstring to PEP 8 standards
            is_valid, msg = validate_line_length(doc, 72)
            if not is_valid:
                doc = wrap_docstring(doc, 72)
            
            # Insert docstring
            insert_at = issue.start_line - 1
            lines = insert_docstring(lines, insert_at, doc)
        except Exception as e:
            print(
                f"[ERROR] Failed to process function at "
                f"line {issue.start_line}: {e}"
            )
            continue
    
    # Write back to file
    try:
        with open(path, "w", encoding="utf8") as f:
            f.write("\n".join(lines))
        return True
    except Exception as e:
        print(f"[ERROR] Could not write {path}: {e}")
        return False

def main():
    """Main hook function."""
    files = get_staged_files()
    
    if not files:
        return 0
    
    changed = False
    for f in files:
        if process_file(f):
            print(f"[ai-docfix] Added docstrings to: {f}")
            changed = True
    
    if changed:
        msg = (
            "[ai-docfix] Docstrings added. "
            "Please review changes, stage them, "
            "and commit again."
        )
        print(msg)
        return 1
    
    return 0