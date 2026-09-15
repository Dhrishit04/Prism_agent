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


class FilesystemSearchSkill(SkillBase):
    """Skill to search for files matching a pattern."""

    @property
    def name(self) -> str:
        return "filesystem.search"

    @property
    def description(self) -> str:
        return "Search for files in the workspace matching a glob pattern."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to search for (e.g., '*.py', '**/*.txt')",
                },
                "path": {
                    "type": "string",
                    "description": "Optional root directory for search (defaults to workspace root)",
                },
            },
            "required": ["pattern"],
        }

    async def execute(self, **kwargs: Any) -> SkillResult:
        pattern = kwargs.get("pattern", "")
        if not pattern:
            return SkillResult.failure("Pattern parameter is required")

        path_str = kwargs.get("path", ".")

        try:
            root_path = Path(path_str).resolve()
            cwd = Path.cwd().resolve()
            
            # Security: ensure search root is within workspace
            if not str(root_path).startswith(str(cwd)):
                return SkillResult.failure(f"Access denied: path outside workspace: {root_path}")
            
            if not root_path.exists() or not root_path.is_dir():
                return SkillResult.failure(f"Search root is not a valid directory: {root_path}")

            matches = []
            # Find all matching files (limit to 100 to avoid huge responses)
            for i, p in enumerate(root_path.glob(pattern)):
                if i >= 100:
                    matches.append("... (results truncated at 100)")
                    break
                
                # Make paths relative to root_path for cleaner output
                try:
                    rel_path = p.relative_to(root_path)
                    matches.append(str(rel_path))
                except ValueError:
                    matches.append(str(p))

            return SkillResult.success({"root": str(root_path), "pattern": pattern, "matches": matches})
        except Exception as e:
            return SkillResult.failure(f"Error searching files: {e}")