import subprocess
import sys
from .parser import find_doc_issues
from .llm import generate_docstring
from .patcher import insert_docstring

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
            # Get snippet for context
            snippet_start = max(0, issue.start_line - 1)
            snippet_end = min(len(lines), issue.start_line + 10)
            snippet = "\n".join(lines[snippet_start:snippet_end])
            
            # Generate docstring
            doc = generate_docstring(snippet)
            
            # Insert docstring
            insert_at = issue.start_line - 1
            lines = insert_docstring(lines, insert_at, doc)
        except Exception as e:
            print(f"[ERROR] Failed to process function at line {issue.start_line}: {e}")
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
        # Stage the changes
        try:
            subprocess.check_call(["git", "add"] + files)
            print("[ai-docfix] Please review the changes and commit again.")
            return 1  # Exit with 1 to prevent commit
        except subprocess.CalledProcessError:
            print("[ERROR] Failed to stage changes")
            return 1
    
    return 0