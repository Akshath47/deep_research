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
    return json.loads(raw)


def write_json(files: Dict[str, str], path: str, obj: Any) -> Dict[str, str]:
    """Write JSON to a file path."""
    files[path] = json.dumps(obj, indent=2, ensure_ascii=False)
    return files


def list_files(files: Dict[str, str], prefix: str = "") -> Dict[str, str]:
    """List all files under a given prefix (e.g., '/summaries/')."""
    return {k: v for k, v in files.items() if k.startswith(prefix)}
