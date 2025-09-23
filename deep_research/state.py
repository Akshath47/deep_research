from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

# Virtual filesystem helpers
from .utils import file_system as vfs


@dataclass
class ResearchFlowState:
    """
    Minimal state container for the Deep Research flow.

    - files: in-memory virtual filesystem {path: content}
    """
    files: Dict[str, str] = field(default_factory=dict)

    # ---- Virtual FS convenience methods ----
    def read_text(self, path: str, *, default: str = "") -> str:
        return vfs.read_text(self.files, path, default=default)

    def write_text(self, path: str, content: str) -> ResearchFlowState:
        vfs.write_text(self.files, path, content)
        return self

    def read_json(self, path: str, default=None) -> Any:
        return vfs.read_json(self.files, path, default=default)

    def write_json(self, path: str, obj: Any) -> ResearchFlowState:
        vfs.write_json(self.files, path, obj)
        return self

    def list_files(self, prefix: str = "") -> Dict[str, str]:
        return vfs.list_files(self.files, prefix)

    def merge_files(self, other: Mapping[str, str] | None) -> ResearchFlowState:
        """
        Merge another files mapping into this state.
        New entries overwrite existing ones (last-write-wins).
        """
        if other:
            self.files.update(other)
        return self

    # ---- Interop helpers (for LangGraph / DeepAgents dict-style state) ----
    def to_state(self) -> Dict[str, Any]:
        return {"files": dict(self.files)}

    @classmethod
    def from_state(cls, state: Mapping[str, Any] | None) -> ResearchFlowState:
        state = state or {}
        files = dict(state.get("files") or {})
        return cls(files=files)
