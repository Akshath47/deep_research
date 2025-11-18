from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import Annotated, Union
from langgraph.prebuilt import InjectedState

from deepagents.prompts import (
    WRITE_TODOS_TOOL_DESCRIPTION,
    LIST_FILES_TOOL_DESCRIPTION,
    READ_FILE_TOOL_DESCRIPTION,
    WRITE_FILE_TOOL_DESCRIPTION,
    EDIT_FILE_TOOL_DESCRIPTION,
)
from deepagents.state import Todo, DeepAgentState


@tool(description=WRITE_TODOS_TOOL_DESCRIPTION)
def write_todos(
    todos: list[Todo], tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(f"Updated todo list to {todos}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool(description=LIST_FILES_TOOL_DESCRIPTION)
def ls(state: Annotated[DeepAgentState, InjectedState]) -> list[str]:
    """List all files"""
    return list(state.get("files", {}).keys())


@tool(description=READ_FILE_TOOL_DESCRIPTION)
def read_file(
    file_path: str,
    state: Annotated[DeepAgentState, InjectedState],
    offset: int = 0,
    limit: int = 2000,
) -> str:
    # Normalize path by removing leading slash for consistency
    normalized_path = file_path.lstrip('/')
    
    mock_filesystem = state.get("files", {})
    if normalized_path not in mock_filesystem:
        return f"Error: File '{file_path}' not found"

    # Get file content using normalized path
    content = mock_filesystem[normalized_path]

    # Handle empty file
    if not content or content.strip() == "":
        return "System reminder: File exists but has empty contents"

    # Split content into lines
    lines = content.splitlines()

    # Apply line offset and limit
    start_idx = offset
    end_idx = min(start_idx + limit, len(lines))

    # Handle case where offset is beyond file length
    if start_idx >= len(lines):
        return f"Error: Line offset {offset} exceeds file length ({len(lines)} lines)"

    # Format output with line numbers (cat -n format)
    result_lines = []
    for i in range(start_idx, end_idx):
        line_content = lines[i]

        # Truncate lines longer than 2000 characters
        if len(line_content) > 2000:
            line_content = line_content[:2000]

        # Line numbers start at 1, so add 1 to the index
        line_number = i + 1
        result_lines.append(f"{line_number:6d}\t{line_content}")

    return "\n".join(result_lines)


@tool(description=WRITE_FILE_TOOL_DESCRIPTION)
def write_file(
    file_path: str,
    content: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    import json
    import re
    
    # Normalize path by removing leading slash for consistency
    normalized_path = file_path.lstrip('/')
    
    # Special handling for JSON files - validate and clean
    if normalized_path.endswith('.json'):
        # Remove markdown code fences if present
        cleaned_content = content.strip()
        if cleaned_content.startswith('```'):
            # Extract content between code fences
            lines = cleaned_content.split('\n')
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's closing fence
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            cleaned_content = '\n'.join(lines).strip()
        
        # Validate JSON and provide helpful error message
        try:
            parsed = json.loads(cleaned_content)
            # Re-serialize to ensure valid formatting
            content = json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            lines = cleaned_content.split('\n')
            error_line = lines[e.lineno - 1] if e.lineno <= len(lines) else "N/A"
            
            error_msg = (
                f"Error: Invalid JSON in {file_path}\n"
                f"Error: {e.msg} at line {e.lineno}, column {e.colno}\n"
                f"Problematic line: {error_line}\n\n"
                f"Common issues:\n"
                f"- Trailing commas after last array/object item\n"
                f"- Unquoted property names\n"
                f"- Comments (not allowed in JSON)\n"
                f"- Single quotes instead of double quotes\n\n"
                f"Please fix the JSON and try again."
            )
            return Command(
                update={
                    "messages": [
                        ToolMessage(error_msg, tool_call_id=tool_call_id)
                    ],
                }
            )
    
    files = state.get("files", {})
    files[normalized_path] = content
    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(f"Updated file {file_path}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool(description=EDIT_FILE_TOOL_DESCRIPTION)
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    replace_all: bool = False,
) -> Union[Command, str]:
    """Write to a file."""
    # Normalize path by removing leading slash for consistency
    normalized_path = file_path.lstrip('/')
    
    mock_filesystem = state.get("files", {})
    # Check if file exists in mock filesystem
    if normalized_path not in mock_filesystem:
        return f"Error: File '{file_path}' not found"

    # Get current file content using normalized path
    content = mock_filesystem[normalized_path]

    # Check if old_string exists in the file
    if old_string not in content:
        return f"Error: String not found in file: '{old_string}'"

    # If not replace_all, check for uniqueness
    if not replace_all:
        occurrences = content.count(old_string)
        if occurrences > 1:
            return f"Error: String '{old_string}' appears {occurrences} times in file. Use replace_all=True to replace all instances, or provide a more specific string with surrounding context."
        elif occurrences == 0:
            return f"Error: String not found in file: '{old_string}'"

    # Perform the replacement
    if replace_all:
        new_content = content.replace(old_string, new_string)
        replacement_count = content.count(old_string)
        result_msg = f"Successfully replaced {replacement_count} instance(s) of the string in '{file_path}'"
    else:
        new_content = content.replace(
            old_string, new_string, 1
        )  # Replace only first occurrence
        result_msg = f"Successfully replaced string in '{file_path}'"

    # Update the mock filesystem using normalized path
    mock_filesystem[normalized_path] = new_content
    return Command(
        update={
            "files": mock_filesystem,
            "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)],
        }
    )
