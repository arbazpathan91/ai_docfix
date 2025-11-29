import subprocess
import sys
from typing import List, Set, Optional, Tuple

from .parser import find_doc_issues
from .llm import generate_docstring
from .patcher import insert_docstring
from .validator import validate_line_length, wrap_docstring

def get_staged_files() -> List[str]:
    try:
        output = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"]
        ).decode().strip()
        if not output: return []
        return [f for f in output.split("\n") if f.endswith(".py")]
    except subprocess.CalledProcessError:
        return []

def get_partially_staged_files() -> Set[str]:
    try:
        output = subprocess.check_output(["git", "diff", "--name-only"]).decode().strip()
        if not output: return set()
        return set(output.split("\n"))
    except subprocess.CalledProcessError:
        return set()

def extract_function_signature(lines: List[str], line_no: int) -> str:
    start = line_no
    sig_lines = [lines[start]]
    i = start + 1
    while (i < len(lines) and i < start + 5):
        line = lines[i].strip()
        if line.endswith(":") and not line.startswith("#"):
            sig_lines.append(lines[i])
            i += 1
            break
        sig_lines.append(lines[i])
        i += 1
    if i < len(lines):
        sig_lines.append(lines[i])
    return (
        "=== FUNCTION/CLASS TO DOCUMENT ===\n" + "\n".join(sig_lines) + "\n=== END FUNCTION/CLASS ==="
    )

def process_file(path: str) -> Tuple[bool, bool]:
    """
    Returns: (was_modified, encountered_errors)
    """
    try:
        with open(path, "r", encoding="utf8") as f:
            original = f.read()
    except Exception as e:
        print(f"[ERROR] Could not read {path}: {e}")
        return False, True
    
    lines = original.split("\n")
    issues = find_doc_issues(original, path)
    
    if not issues:
        return False, False
    
    issues.sort(key=lambda x: x.start_line, reverse=True)
    successful_updates = 0
    errors = False
    
    for issue in issues:
        try:
            func_signature = extract_function_signature(lines, issue.start_line - 1)
            doc = generate_docstring(func_signature, full_file_context=original)
            
            if not doc:
                # IMPORTANT: If we found an issue but got no doc, that's an ERROR.
                # We flag it so we can fail the hook and show logs.
                print(f"[ERROR] LLM failed to generate docstring for line {issue.start_line} in {path}")
                errors = True
                continue
            
            doc = doc.strip()
            if doc.startswith('"""') or doc.startswith("'''"): doc = doc[3:]
            if doc.endswith('"""') or doc.endswith("'''"): doc = doc[:-3]
            doc = doc.strip()
            
            doc = wrap_docstring(doc, 72)
            lines = insert_docstring(lines, issue.start_line - 1, doc)
            successful_updates += 1
            
        except Exception as e:
            print(f"[ERROR] Processing exception at line {issue.start_line}: {e}")
            errors = True
            continue
    
    if successful_updates > 0:
        try:
            with open(path, "w", encoding="utf8") as f:
                f.write("\n".join(lines))
            return True, errors
        except Exception as e:
            print(f"[ERROR] Could not write {path}: {e}")
            return False, True
            
    return False, errors

def main(files: Optional[List[str]] = None) -> int:
    if not files:
        files = get_staged_files()
    
    if not files:
        return 0
    
    # 1. Block Partial Staging
    dirty_files = get_partially_staged_files()
    overlapping = [f for f in files if f in dirty_files]
    if overlapping:
        print("\n[!] STOPPING COMMIT: Staged files have unstaged changes on disk.")
        print("    This usually happens if you generated docs but forgot to 'git add' them.")
        print("    Files:")
        for f in overlapping:
            print(f"     - {f}")
        print("\n    ACTION: Run 'git add <file>' then commit again.\n")
        return 1

    any_changes = False
    any_errors = False

    for f in files:
        try:
            with open(f, 'r'): pass
        except FileNotFoundError:
            continue

        changed, error = process_file(f)
        if changed:
            print(f"[ai-docfix] Added docstrings to: {f}")
            any_changes = True
        if error:
            any_errors = True
    
    # 2. Logic for Exit Codes
    if any_changes:
        print("\n[ai-docfix] Docstrings generated. Please 'git add' them and commit again.")
        return 1
    
    if any_errors:
        print("\n[ai-docfix] Failed to generate some docstrings. See logs above.")
        # We return 1 so pre-commit shows the error logs (stdout/stderr)
        return 1
    
    return 0