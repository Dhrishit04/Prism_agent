"""Unified automation orchestrator for Prism."""

from enum import Enum
from typing import Any


class AutomationMode(Enum):
    WEB = "web"
    DESKTOP = "desktop"
    OFFICE = "office"


class AutomationOrchestrator:
    """Decides which automation subsystem to use and manages sessions."""

    def __init__(self):
        self.web_automation: Any = None
        self.mode: AutomationMode = AutomationMode.WEB

    async def start_web(self, headless: bool = True, timeout: int = 30000):
        """Start web automation session."""
        from automation.browser import WebAutomation
        self.web_automation = WebAutomation(headless=headless, timeout=timeout)
        await self.web_automation.__aenter__()
        self.mode = AutomationMode.WEB

    async def stop_web(self):
        """Stop web automation session."""
        if self.web_automation:
            await self.web_automation.close()
            self.web_automation = None

    async def execute_web_action(self, action: str, **kwargs) -> dict[str, Any]:
        """Execute web automation action."""
        if not self.web_automation:
            return {"success": False, "error": "Web automation not started. Call start_web first."}

        actions = {
            "navigate": self.web_automation.navigate,
            "click": self.web_automation.click,
            "type": self.web_automation.type,
            "select": self.web_automation.select,
            "extract": self.web_automation.extract,
            "screenshot": self.web_automation.screenshot,
            "get_page_content": self.web_automation.get_page_content,
            "wait_for": self.web_automation.wait_for,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            result = await actions[action](**kwargs)
            # Wrap successful results in standard format
            if isinstance(result, dict) and "success" not in result:
                return {"success": True, **result}
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    @property
    def web_active(self) -> bool:
        """Check if web automation is active."""
        return self.web_automation is not None

    def get_status(self) -> dict[str, Any]:
        """Get automation status."""
        return {
            "mode": self.mode.value,
            "web_active": self.web_active,
        }