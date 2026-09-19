"""Web and Desktop Automation module for Prism."""

from automation.browser import WebAutomation
from automation.desktop import DesktopAutomation, get_desktop_automation, reset_desktop_automation
from automation.orchestrator import AutomationOrchestrator, get_automation_orchestrator

__all__ = ["WebAutomation", "DesktopAutomation", "get_desktop_automation", "reset_desktop_automation", "AutomationOrchestrator", "get_automation_orchestrator"]