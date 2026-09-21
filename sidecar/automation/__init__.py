"""Web and Desktop Automation module for Tesseract."""

from automation.browser import WebAutomation
from automation.office import OfficeAutomation, get_office_automation
from automation.orchestrator import AutomationOrchestrator, get_automation_orchestrator

__all__ = [
    "WebAutomation",
    "OfficeAutomation",
    "get_office_automation",
    "DesktopAutomation",
    "get_desktop_automation",
    "reset_desktop_automation",
    "AutomationOrchestrator",
    "get_automation_orchestrator",
]


def __getattr__(name: str):
    if name in {"DesktopAutomation", "get_desktop_automation", "reset_desktop_automation"}:
        from automation.desktop import DesktopAutomation, get_desktop_automation, reset_desktop_automation
        return {
            "DesktopAutomation": DesktopAutomation,
            "get_desktop_automation": get_desktop_automation,
            "reset_desktop_automation": reset_desktop_automation,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")