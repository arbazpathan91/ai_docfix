import subprocess
import sys
from .parser import find_doc_issues
from .llm import generate_docstring
from .patcher import insert_docstring

def get_staged_files():
    """Get staged Python files from git."""
    output = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"]
    ).decode().strip().split("\n")
    return [f for f in output if f.endswith(".py")]

def process_file(path):
    """Process a single file to add missing docstrings."""
    with open(path, "r", encoding="utf8") as f:
        original = f.read()
    
    lines = original.split("\n")
    issues = find_doc_issues(original, path)
    
    if not issues:
        return False
    
    # Sort issues in reverse order to avoid line number shifting
    issues.sort(key=lambda x: x.start_line, reverse=True)
    
    for issue in issues:
        snippet_start = max(0, issue.start_line - 1)
        snippet_end = min(len(lines), issue.start_line + 10)
        snippet = "\n".join(lines[snippet_start:snippet_end])
        
        try:
            doc = generate_docstring(snippet)
        except Exception as e:
            print(f"[ERROR] Failed to generate docstring for {path}: {e}")
            continue
        
        insert_at = issue.start_line - 1
        lines = insert_docstring(lines, insert_at, doc)
    
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(lines))
    
    return True

def main():
    """Main hook function."""
    files = get_staged_files()
    
    changed = False
    for f in files:
        try:
            if process_file(f):
                print(f"[ai-docfix] Updated documentation in: {f}")
                changed = True
        except Exception as e:
            print(f"[ERROR] Error processing {f}: {e}")
            continue
    
    if changed:
        print("Re-staging modified files...")
        subprocess.check_call(["git", "add"] + files)
        print("Documentation added. Please commit again.")
        sys.exit(1)
    
    return 0
