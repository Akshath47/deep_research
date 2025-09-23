from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping
from deepagents.state import DeepAgentState

# Virtual filesystem helpers
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import file_system as vfs


class ResearchFlowState(DeepAgentState):
    """
    State container for the Deep Research flow that extends DeepAgentState.

    - files: in-memory virtual filesystem {path: content} (inherited from DeepAgentState)
    - todos: task tracking (inherited from DeepAgentState)
    """
    pass  # files field is already defined in DeepAgentState

    pass  # All methods will be utility functions since TypedDict doesn't support methods


# ---- Utility functions for ResearchFlowState ----
def read_text(state: ResearchFlowState, path: str, *, default: str = "") -> str:
    return vfs.read_text(state.get("files", {}), path, default=default)


def write_text(state: ResearchFlowState, path: str, content: str) -> None:
    files = dict(state.get("files", {}))
    vfs.write_text(files, path, content)
    state["files"] = files


def read_json(state: ResearchFlowState, path: str, default=None) -> Any:
    return vfs.read_json(state.get("files", {}), path, default=default)


def write_json(state: ResearchFlowState, path: str, obj: Any) -> None:
    files = dict(state.get("files", {}))
    vfs.write_json(files, path, obj)
    state["files"] = files


def list_files(state: ResearchFlowState, prefix: str = "") -> Dict[str, str]:
    return vfs.list_files(state.get("files", {}), prefix)


def merge_files(state: ResearchFlowState, other: Mapping[str, str] | None) -> None:
    """
    Merge another files mapping into this state.
    New entries overwrite existing ones (last-write-wins).
    """
    if other:
        files = dict(state.get("files", {}))
        files.update(other)
        state["files"] = files
