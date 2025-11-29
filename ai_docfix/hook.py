import subprocess
import sys
from typing import List, Optional

from .parser import find_doc_issues
from .llm import generate_docstring
from .patcher import insert_docstring
from .validator import validate_line_length, wrap_docstring

def get_staged_files() -> List[str]:
    """Get staged Python files from git."""
    try:
        # Check against the HEAD to see what is staged
        output = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"]
        ).decode().strip()
        
        if not output:
            return []
            
        return [f for f in output.split("\n") if f.endswith(".py")]
    except subprocess.CalledProcessError:
        # Not a git repo or git error
        return []

def extract_function_signature(lines: List[str], line_no: int) -> str:
    """
    Extract function signature with clear markers.
    
    Captures the definition line and up to 5 subsequent lines to 
    handle multi-line arguments, plus a bit of the body for context.
    """
    start = line_no
    sig_lines = [lines[start]]
    i = start + 1

    # Collect full signature (heuristically up to 5 lines)
    # Stop if we hit the end of the signature or indentation changes significantly
    while (i < len(lines) and i < start + 5):
        line = lines[i].strip()
        
        # Heuristic to detect end of signature or start of body
        if line.endswith(":") and not line.startswith("#"):
            sig_lines.append(lines[i])
            i += 1
            break
            
        sig_lines.append(lines[i])
        i += 1

    # Add 1 line of body context to help LLM understand logic
    if i < len(lines):
        sig_lines.append(lines[i])

    signature = "\n".join(sig_lines)

    return (
        "=== FUNCTION/CLASS TO DOCUMENT ===\n" +
        signature +
        "\n=== END FUNCTION/CLASS ==="
    )

def process_file(path: str) -> bool:
    """
    Process a single file to add missing docstrings.
    Returns True if file was modified.
    """
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
    
    # Sort issues in reverse order to avoid line number shifting during insertion
    issues.sort(key=lambda x: x.start_line, reverse=True)
    
    successful_updates = 0
    
    for issue in issues:
        try:
            # Extract context
            func_signature = extract_function_signature(
                lines, issue.start_line - 1
            )
            
            # Generate docstring via LiteLLM
            doc = generate_docstring(
                function_signature=func_signature,
                full_file_context=original
            )
            
            if not doc:
                print(
                    f"[WARNING] Skipping {issue.node.name} at line {issue.start_line}: "
                    f"LLM returned empty response."
                )
                continue
            
            # Defensive Cleanup: Ensure no enclosing quotes exist before wrapping
            # (llm.py handles this mostly, but this is a safety net)
            doc = doc.strip()
            if doc.startswith('"""') or doc.startswith("'''"):
                doc = doc[3:]
            if doc.endswith('"""') or doc.endswith("'''"):
                doc = doc[:-3]
            doc = doc.strip()
            
            # Formatting: Validate and Wrap
            # We trust validator.wrap_docstring to handle indentation and length
            doc = wrap_docstring(doc, 72)
            
            # Insert into file lines
            insert_at = issue.start_line - 1
            lines = insert_docstring(lines, insert_at, doc)
            successful_updates += 1
            
        except Exception as e:
            print(
                f"[WARNING] Failed to process function at "
                f"line {issue.start_line}: {e}"
            )
            continue
    
    if successful_updates == 0:
        return False
    
    # Write back to file
    try:
        with open(path, "w", encoding="utf8") as f:
            f.write("\n".join(lines))
        return True
    except Exception as e:
        print(f"[ERROR] Could not write {path}: {e}")
        return False

def main(files: Optional[List[str]] = None) -> int:
    """
    Main hook entry point.
    
    Args:
        files: Optional list of files to process. 
               If None, attempts to find staged git files.
    """
    if not files:
        files = get_staged_files()
    
    if not files:
        print("[INFO] No files to process (no args provided and no staged files found).")
        return 0
    
    changed = False
    for f in files:
        # Simple existence check
        try:
            with open(f, 'r'): pass
        except FileNotFoundError:
            print(f"[WARNING] File not found: {f}")
            continue

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