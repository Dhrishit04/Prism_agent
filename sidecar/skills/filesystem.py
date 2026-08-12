"""Example filesystem skill for testing the skill system."""

import os
from pathlib import Path
from typing import Any

from skills.skill_base import SkillBase, SkillResult


class FilesystemReadFileSkill(SkillBase):
    """Skill to read a file from the filesystem."""

    @property
    def name(self) -> str:
        return "filesystem.read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file from the local filesystem."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read (relative to workspace or absolute)",
                },
            },
            "required": ["path"],
        }

    async def execute(self, **kwargs: Any) -> SkillResult:
        path_str = kwargs.get("path", "")
        if not path_str:
            return SkillResult.failure("Path parameter is required")

        try:
            path = Path(path_str).resolve()
            # Security: only allow reading from current working directory or subdirectories
            cwd = Path.cwd().resolve()
            if not str(path).startswith(str(cwd)):
                return SkillResult.failure(f"Access denied: path outside workspace: {path}")

            if not path.exists():
                return SkillResult.failure(f"File not found: {path}")

            if not path.is_file():
                return SkillResult.failure(f"Path is not a file: {path}")

            content = path.read_text(encoding="utf-8")
            return SkillResult.success({"path": str(path), "content": content})
        except Exception as e:
            return SkillResult.failure(f"Error reading file: {e}")


class FilesystemListDirSkill(SkillBase):
    """Skill to list a directory's contents."""

    @property
    def name(self) -> str:
        return "filesystem.list_directory"

    @property
    def description(self) -> str:
        return "List the contents of a directory."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory to list (relative to workspace or absolute)",
                },
            },
            "required": ["path"],
        }

    async def execute(self, **kwargs: Any) -> SkillResult:
        path_str = kwargs.get("path", "")
        if not path_str:
            return SkillResult.failure("Path parameter is required")

        try:
            path = Path(path_str).resolve()
            cwd = Path.cwd().resolve()
            if not str(path).startswith(str(cwd)):
                return SkillResult.failure(f"Access denied: path outside workspace: {path}")

            if not path.exists():
                return SkillResult.failure(f"Directory not found: {path}")

            if not path.is_dir():
                return SkillResult.failure(f"Path is not a directory: {path}")

            entries = []
            for entry in path.iterdir():
                entries.append(
                    {
                        "name": entry.name,
                        "type": "directory" if entry.is_dir() else "file",
                        "path": str(entry),
                    }
                )

            return SkillResult.success({"path": str(path), "entries": entries})
        except Exception as e:
            return SkillResult.failure(f"Error listing directory: {e}")


class FilesystemWriteFileSkill(SkillBase):
    """Skill to write a file to the filesystem."""

    @property
    def name(self) -> str:
        return "filesystem.write_file"

    @property
    def description(self) -> str:
        return "Write content to a file on the local filesystem."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write (relative to workspace or absolute)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        }

    async def execute(self, **kwargs: Any) -> SkillResult:
        path_str = kwargs.get("path", "")
        content = kwargs.get("content", "")

        if not path_str:
            return SkillResult.failure("Path parameter is required")

        try:
            path = Path(path_str).resolve()
            cwd = Path.cwd().resolve()
            if not str(path).startswith(str(cwd)):
                return SkillResult.failure(f"Access denied: path outside workspace: {path}")

            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding="utf-8")
            return SkillResult.success({"path": str(path), "bytes_written": len(content.encode())})
        except Exception as e:
            return SkillResult.failure(f"Error writing file: {e}")