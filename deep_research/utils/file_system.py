import json
from typing import Dict, Any


def read_text(files: Dict[str, str], path: str, default: str = "") -> str:
    """Read plain text, return default if not found."""
    return files.get(path, default)


def write_text(files: Dict[str, str], path: str, content: str) -> Dict[str, str]:
    """Write plain text to a file path."""
    files[path] = content
    return files


def read_json(files: Dict[str, str], path: str, default=None) -> Any:
    """Read JSON, return default if not found."""
    raw = files.get(path)
    if raw is None:
        return default if default is not None else []
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # Provide detailed error message with context
        lines = raw.split('\n')
        error_line = lines[e.lineno - 1] if e.lineno <= len(lines) else "N/A"
        
        # Show surrounding context (3 lines before/after)
        start = max(0, e.lineno - 4)
        end = min(len(lines), e.lineno + 3)
        context = '\n'.join(f"{i+1:4d} | {lines[i]}" for i in range(start, end))
        
        error_msg = (
            f"Failed to parse JSON from '{path}':\n"
            f"Error: {e.msg} at line {e.lineno}, column {e.colno}\n"
            f"Problematic line: {error_line}\n"
            f"\nContext:\n{context}\n"
            f"\nFull content (first 500 chars):\n{raw[:500]}"
        )
        raise ValueError(error_msg) from e


def write_json(files: Dict[str, str], path: str, obj: Any) -> Dict[str, str]:
    """Write JSON to a file path."""
    files[path] = json.dumps(obj, indent=2, ensure_ascii=False)
    return files


def list_files(files: Dict[str, str], prefix: str = "") -> Dict[str, str]:
    """List all files under a given prefix (e.g., '/summaries/')."""
    return {k: v for k, v in files.items() if k.startswith(prefix)}
