"""Tesseract Skills Package.

This package contains the skill system for Tesseract AI Agent.
Skills are auto-discovered from this directory at startup.
"""

from skills.registry import SkillRegistry, get_registry, reset_registry
from skills.skill_base import SkillBase, SkillResult

__all__ = [
    "SkillBase",
    "SkillResult",
    "SkillRegistry",
    "get_registry",
    "reset_registry",
]