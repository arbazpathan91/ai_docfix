import subprocess
import sys
import re
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
    """
    Extract ONLY the function/class signature (up to the colon).
    Does not include body code to prevent LLM confusion.
    """
    sig_lines = []
    i = line_no
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip comments if they appear before the def/class (rare given line_no comes from AST)
        if stripped.startswith('#'):
            sig_lines.append(line)
            i += 1
            continue
            
        sig_lines.append(line)
        
        # Check if this line ends the signature
        # 1. Ends with ':' (standard)
        # 2. Ends with ':\s*#.*' (colon followed by comment)
        if ':' in stripped:
            # check if colon is the last significant char (ignoring comments)
            pre_comment = stripped.split('#')[0].strip()
            if pre_comment.endswith(':'):
                break
        
        i += 1
        # Safety break to prevent grabbing the whole file if syntax is weird
        if i > line_no + 10: 
            break

    return "\n".join(sig_lines)

def process_file(path: str) -> Tuple[bool, bool]:
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
            # 1. Extract strictly the signature
            func_signature = extract_function_signature(lines, issue.start_line - 1)
            
            # 2. Generate
            doc = generate_docstring(func_signature, full_file_context=original)
            
            if not doc:
                print(f"[ERROR] LLM failed to generate docstring for line {issue.start_line} in {path}")
                errors = True
                continue
            
            # 3. Clean
            doc = doc.strip()
            if doc.startswith('"""') or doc.startswith("'''"): doc = doc[3:]
            if doc.endswith('"""') or doc.endswith("'''"): doc = doc[:-3]
            doc = doc.strip()
            
            # 4. Wrap & Patch
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
    
    # Block Partial Staging
    dirty_files = get_partially_staged_files()
    overlapping = [f for f in files if f in dirty_files]
    if overlapping:
        print("\n[!] STOPPING COMMIT: Staged files have unstaged changes on disk.")
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
    
    if any_changes:
        print("\n[ai-docfix] Docstrings generated. Please 'git add' them and commit again.")
        return 1
    
    if any_errors:
        print("\n[ai-docfix] Failed to generate some docstrings. See logs above.")
        return 1
    
    return 0