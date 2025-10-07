import posixpath

from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import Annotated, Union, Literal, Optional
from langgraph.prebuilt import InjectedState

from deepagents.prompts import (
    WRITE_TODOS_DESCRIPTION,
    EDIT_DESCRIPTION,
    READ_TOOL_DESCRIPTION,
    WRITE_TOOL_DESCRIPTION,
)
from deepagents.state import Todo, DeepAgentState

_FILE_ROOT_PREFIXES = ("/mnt/data", "/ubuntu/data")


def _normalize_file_key(file_path: str) -> str:
    """将文件路径归一化为兼容状态字典的形式。"""
    if not file_path:
        return ""

    # 统一分隔符并清理多余的 . 与 ..
    posix_path = posixpath.normpath(file_path.replace("\\", "/").strip())

    # 移除常见的容器根路径前缀
    for prefix in _FILE_ROOT_PREFIXES:
        if posix_path == prefix:
            posix_path = ""
            break
        if posix_path.startswith(prefix + "/"):
            posix_path = posix_path[len(prefix) + 1 :]
            break

    # 去掉可能残留的绝对路径前缀
    if posix_path.startswith("/"):
        posix_path = posix_path[1:]

    # normpath 对空字符串会返回 "."，这里转为空字符串保持语义
    if posix_path == ".":
        return ""

    return posix_path


def _resolve_file_key(
    files: Optional[dict[str, str]], file_path: str
) -> tuple[Optional[str], str]:
    """查找输入路径对应的真实键，并返回归一化后的路径表示。"""

    files = files or {}
    normalized_key = _normalize_file_key(file_path)

    if file_path in files:
        return file_path, normalized_key

    if normalized_key and normalized_key in files:
        return normalized_key, normalized_key

    for existing_key in files.keys():
        if _normalize_file_key(existing_key) == normalized_key:
            return existing_key, normalized_key

    return None, normalized_key


@tool(description=WRITE_TODOS_DESCRIPTION)
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


def ls(state: Annotated[DeepAgentState, InjectedState]) -> list[str]:
    """List all files"""
    return list(state.get("files", {}).keys())


@tool(description=READ_TOOL_DESCRIPTION)
def read_file(
    file_path: str,
    state: Annotated[DeepAgentState, InjectedState],
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """Read file."""
    mock_filesystem = state.get("files", {}) or {}
    matched_key, normalized_key = _resolve_file_key(mock_filesystem, file_path)
    if matched_key is None:
        if normalized_key and normalized_key != file_path:
            return (
                f"Error: File '{file_path}' not found (归一化路径: '{normalized_key}')"
            )
        return f"Error: File '{file_path}' not found"

    # Get file content
    content = mock_filesystem[matched_key]

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


@tool(description=WRITE_TOOL_DESCRIPTION)
def write_file(
    file_path: str,
    content: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    mode: Literal["overwrite", "append"] = "overwrite",
    add_newline: bool = True,
) -> Command:
    """写入或追加内容到文件"""
    files = state.get("files", {}) or {}
    matched_key, normalized_key = _resolve_file_key(files, file_path)
    if matched_key is not None:
        target_key = matched_key
    else:
        target_key = normalized_key or file_path

    if mode == "append":
        existing_content = files.get(target_key, "")

        if add_newline and existing_content and not existing_content.endswith('\n'):
            new_content = existing_content + '\n' + content
        else:
            new_content = existing_content + content

        action_msg = f"追加内容到文件 {target_key}"
    else:
        new_content = content
        action_msg = f"更新文件 {target_key}"

    files[target_key] = new_content

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(action_msg, tool_call_id=tool_call_id)
            ],
        }
    )


@tool(description=EDIT_DESCRIPTION)
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    replace_all: bool = False,
) -> Union[Command, str]:
    """Write to a file."""
    mock_filesystem = state.get("files", {}) or {}
    matched_key, normalized_key = _resolve_file_key(mock_filesystem, file_path)

    if matched_key is None:
        if normalized_key and normalized_key != file_path:
            return (
                f"Error: File '{file_path}' not found (归一化路径: '{normalized_key}')"
            )
        return f"Error: File '{file_path}' not found"

    # Get current file content
    content = mock_filesystem[matched_key]

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
        mock_filesystem[matched_key] = new_content
        result_msg = f"Successfully replaced {replacement_count} instance(s) of the string in '{matched_key}'"
    else:
        new_content = content.replace(
            old_string, new_string, 1
        )  # Replace only first occurrence
        mock_filesystem[matched_key] = new_content
        result_msg = f"Successfully replaced string in '{matched_key}'"
    return Command(
        update={
            "files": mock_filesystem,
            "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)],
        }
    )
