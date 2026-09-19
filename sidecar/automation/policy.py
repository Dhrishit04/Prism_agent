"""Shared automation settings policy."""

import json
import os


def load_automation_policy() -> dict[str, bool]:
    """Return the configured automation and OCR permissions."""
    path = os.path.join(os.path.expanduser("~"), ".prism", "settings.json")
    try:
        with open(path, "r") as settings_file:
            settings = json.load(settings_file)
    except (OSError, ValueError):
        settings = {}

    automation = settings.get("automation", {})
    return {
        "automation_enabled": bool(automation.get("automation_enabled", False)),
        "ocr_enabled": bool(automation.get("ocr_enabled", False)),
    }
