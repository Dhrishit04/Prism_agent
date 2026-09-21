"""Desktop GUI automation for Tesseract using Windows UIA (pywinauto) and OCR fallback."""

import base64
import logging
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from PIL import Image, ImageGrab
import io

# Try to import Windows UIA automation
try:
    import pywinauto
    from pywinauto import Desktop, Application
    from pywinauto.findwindows import ElementNotFoundError
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    pywinauto = None
    Desktop = None
    Application = None
    ElementNotFoundError = Exception

# Try to import OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

# Try to import PyAutoGUI for fallback
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    pyautogui = None

logger = logging.getLogger(__name__)


@dataclass
class UIElement:
    """Represents a UI element from the accessibility tree."""
    name: str
    control_type: str
    rectangle: dict[str, int]  # left, top, right, bottom
    class_name: str
    automation_id: str
    is_enabled: bool
    is_visible: bool
    children: list["UIElement"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "control_type": self.control_type,
            "rectangle": self.rectangle,
            "class_name": self.class_name,
            "automation_id": self.automation_id,
            "is_enabled": self.is_enabled,
            "is_visible": self.is_visible,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class WindowInfo:
    """Information about a window."""
    handle: int
    title: str
    class_name: str
    process_id: int
    rectangle: dict[str, int]
    is_visible: bool
    is_minimized: bool
    is_maximized: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "handle": self.handle,
            "title": self.title,
            "class_name": self.class_name,
            "process_id": self.process_id,
            "rectangle": self.rectangle,
            "is_visible": self.is_visible,
            "is_minimized": self.is_minimized,
            "is_maximized": self.is_maximized,
        }


class DesktopAutomation:
    """Desktop GUI automation engine using Windows UIA with OCR fallback."""

    def __init__(self, ocr_enabled: bool = False):
        self.ocr_enabled = ocr_enabled and TESSERACT_AVAILABLE
        self._app: Optional[Any] = None
        self._current_window: Optional[Any] = None
        self._window_handle: Optional[int] = None

    def find_window(self, title: str, class_name: str = None, process_name: str = None) -> dict[str, Any]:
        """Find and optionally activate a window by title, class, or process name."""
        if not PYWINAUTO_AVAILABLE:
            return {"success": False, "error": "pywinauto not available. Install with: pip install pywinauto"}

        try:
            # Build search criteria.
            criteria = {}
            if title:
                criteria["title_re"] = title
            if class_name:
                criteria["class_name"] = class_name
            if process_name:
                process_ids = self._resolve_process_ids(process_name)
                if not process_ids:
                    return {"success": False, "error": f"No process found matching name: {process_name}"}
                criteria["process"] = process_ids[0]

            if not criteria:
                return {"success": False, "error": "Window selection criteria cannot be empty; provide title, class_name, or process_name."}

            if process_name and len(process_ids) > 1:
                windows = []
                for process_id in process_ids:
                    windows.extend(Desktop(backend="uia").windows(**{**criteria, "process": process_id}))
            else:
                windows = Desktop(backend="uia").windows(**criteria)
            if not windows:
                return {"success": False, "error": f"No window found matching criteria: {criteria}"}

            # Use the first match - get a WindowSpecification for element searching
            window = windows[0]
            handle = window.handle
            self._window_handle = handle

            # Create a WindowSpecification for element searching (this supports child_window)
            self._current_window = Desktop(backend="uia").window(handle=handle)

            # Get window info
            rect = window.rectangle()
            info = WindowInfo(
                handle=handle,
                title=window.window_text(),
                class_name=window.class_name(),
                process_id=window.process_id(),
                rectangle={"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom},
                is_visible=window.is_visible(),
                is_minimized=window.is_minimized(),
                is_maximized=window.is_maximized(),
            )

            return {"success": True, "window": info.to_dict()}

        except ElementNotFoundError:
            return {"success": False, "error": f"Window not found: {criteria}"}
        except Exception as e:
            logger.error(f"Error finding window: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _resolve_process_ids(process_name: str) -> list[int]:
        """Resolve an executable name to process IDs accepted by pywinauto."""
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=True,
        )
        process_ids = []
        for line in result.stdout.splitlines():
            fields = [field.strip('"') for field in line.split('","')]
            if len(fields) >= 2 and fields[1].isdigit():
                process_ids.append(int(fields[1]))
        return process_ids

    def focus_window(self, handle: int = None) -> dict[str, Any]:
        """Focus a window by handle (or current window if not specified)."""
        if not PYWINAUTO_AVAILABLE:
            return {"success": False, "error": "pywinauto not available"}

        try:
            hwnd = handle or self._window_handle
            if not hwnd:
                return {"success": False, "error": "No window handle specified"}

            window = Desktop(backend="uia").window(handle=hwnd)
            window.set_focus()
            self._current_window = window
            self._window_handle = hwnd

            return {"success": True, "handle": hwnd}

        except Exception as e:
            logger.error(f"Error focusing window: {e}")
            return {"success": False, "error": str(e)}

    def get_ui_elements(self, max_depth: int = 3, include_children: bool = True) -> dict[str, Any]:
        """Get the accessibility tree for the current window."""
        if not PYWINAUTO_AVAILABLE:
            return {"success": False, "error": "pywinauto not available"}

        if not self._current_window:
            return {"success": False, "error": "No window selected. Call find_window first."}

        try:
            def build_element_tree(element, depth=0):
                if depth > max_depth:
                    return None

                try:
                    rect = element.rectangle()
                    ui_element = UIElement(
                        name=element.window_text() or "",
                        control_type=element.element_info.control_type,
                        rectangle={"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom},
                        class_name=element.class_name(),
                        automation_id=element.element_info.automation_id or "",
                        is_enabled=element.is_enabled(),
                        is_visible=element.is_visible(),
                    )

                    if include_children and depth < max_depth:
                        try:
                            children = element.children()
                            for child in children:
                                child_tree = build_element_tree(child, depth + 1)
                                if child_tree:
                                    ui_element.children.append(child_tree)
                        except Exception:
                            pass

                    return ui_element
                except Exception:
                    return None

            root = build_element_tree(self._current_window)
            if not root:
                return {"success": False, "error": "Failed to build element tree"}

            return {"success": True, "elements": root.to_dict()}

        except Exception as e:
            logger.error(f"Error getting UI elements: {e}")
            return {"success": False, "error": str(e)}

    def click_element(self, name: str = None, control_type: str = None, automation_id: str = None,
                      coordinates: tuple[int, int] = None) -> dict[str, Any]:
        """Click a UI element by name, type, automation_id, or coordinates."""
        if not PYWINAUTO_AVAILABLE and not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "No automation backend available (need pywinauto or pyautogui)"}

        try:
            # If coordinates provided, use PyAutoGUI
            if coordinates and PYAUTOGUI_AVAILABLE:
                x, y = coordinates
                pyautogui.click(x, y)
                return {"success": True, "method": "pyautogui", "coordinates": coordinates}

            if not self._current_window:
                return {"success": False, "error": "No window selected. Call find_window first."}

            # Build search criteria
            criteria = {}
            if name:
                criteria["title"] = name
            if control_type:
                criteria["control_type"] = control_type
            if automation_id:
                criteria["automation_id"] = automation_id

            if not criteria:
                return {"success": False, "error": "At least one search criterion required"}

            # Find element
            element = self._current_window.child_window(**criteria)
            if not element.exists():
                return {"success": False, "error": f"Element not found: {criteria}"}

            # Click the element
            element.click_input()
            return {"success": True, "method": "pywinauto", "criteria": criteria}

        except ElementNotFoundError:
            return {"success": False, "error": f"Element not found: {criteria}"}
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return {"success": False, "error": str(e)}

    def type_text(self, text: str, name: str = None, control_type: str = None,
                  automation_id: str = None, coordinates: tuple[int, int] = None) -> dict[str, Any]:
        """Type text into a UI element."""
        if not PYWINAUTO_AVAILABLE and not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "No automation backend available"}

        try:
            # If coordinates provided, use PyAutoGUI
            if coordinates and PYAUTOGUI_AVAILABLE:
                x, y = coordinates
                pyautogui.click(x, y)
                time.sleep(0.1)
                pyautogui.write(text)
                return {"success": True, "method": "pyautogui", "text": text}

            if not self._current_window:
                return {"success": False, "error": "No window selected. Call find_window first."}

            criteria = {}
            if name:
                criteria["title"] = name
            if control_type:
                criteria["control_type"] = control_type
            if automation_id:
                criteria["automation_id"] = automation_id

            if not criteria:
                return {"success": False, "error": "At least one search criterion required"}

            element = self._current_window.child_window(**criteria)
            if not element.exists():
                return {"success": False, "error": f"Element not found: {criteria}"}

            element.set_focus()
            set_edit_text = getattr(element, "set_edit_text", None)
            if callable(set_edit_text):
                set_edit_text(text)
            else:
                escaped_text = text
                for token in ("%", "+", "^", "~", "(", ")", "{", "}"):
                    escaped_text = escaped_text.replace(token, "{" + token + "}")
                element.type_keys(escaped_text, with_spaces=True)
            return {"success": True, "method": "pywinauto", "text": text}

        except ElementNotFoundError:
            return {"success": False, "error": f"Element not found: {criteria}"}
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return {"success": False, "error": str(e)}

    def get_element_text(self, name: str = None, control_type: str = None,
                         automation_id: str = None) -> dict[str, Any]:
        """Get text from a UI element."""
        if not PYWINAUTO_AVAILABLE:
            return {"success": False, "error": "pywinauto not available"}

        if not self._current_window:
            return {"success": False, "error": "No window selected. Call find_window first."}

        try:
            criteria = {}
            if name:
                criteria["title"] = name
            if control_type:
                criteria["control_type"] = control_type
            if automation_id:
                criteria["automation_id"] = automation_id

            if not criteria:
                return {"success": False, "error": "At least one search criterion required"}

            element = self._current_window.child_window(**criteria)
            if not element.exists():
                return {"success": False, "error": f"Element not found: {criteria}"}

            text = element.window_text()
            return {"success": True, "text": text}

        except ElementNotFoundError:
            return {"success": False, "error": f"Element not found: {criteria}"}
        except Exception as e:
            logger.error(f"Error getting element text: {e}")
            return {"success": False, "error": str(e)}

    def screenshot(self, region: tuple[int, int, int, int] = None, full_screen: bool = False) -> dict[str, Any]:
        """Take a screenshot of the screen, window, or region."""
        try:
            if full_screen:
                img = ImageGrab.grab()
            elif region:
                img = ImageGrab.grab(bbox=region)
            elif self._current_window and PYWINAUTO_AVAILABLE:
                rect = self._current_window.rectangle()
                img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
            else:
                img = ImageGrab.grab()

            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            return {
                "success": True,
                "image_base64": img_base64,
                "width": img.width,
                "height": img.height,
                "region": region,
            }

        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {"success": False, "error": str(e)}

    def ocr(self, region: tuple[int, int, int, int] = None, image_base64: str = None) -> dict[str, Any]:
        """Extract text from an image region using Tesseract OCR."""
        if not self.ocr_enabled:
            return {"success": False, "error": "OCR not enabled or Tesseract not available"}

        try:
            if image_base64:
                # Decode base64 image
                img_data = base64.b64decode(image_base64)
                img = Image.open(io.BytesIO(img_data))
            elif region:
                img = ImageGrab.grab(bbox=region)
            elif self._current_window and PYWINAUTO_AVAILABLE:
                rect = self._current_window.rectangle()
                img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
            else:
                img = ImageGrab.grab()

            # Run OCR
            text = pytesseract.image_to_string(img)
            return {"success": True, "text": text.strip()}

        except Exception as e:
            logger.error(f"Error running OCR: {e}")
            return {"success": False, "error": str(e)}

    def resize_window(self, handle: int = None, width: int = None, height: int = None) -> dict[str, Any]:
        """Resize a window."""
        if not PYWINAUTO_AVAILABLE:
            return {"success": False, "error": "pywinauto not available"}

        try:
            hwnd = handle or self._window_handle
            if not hwnd:
                return {"success": False, "error": "No window handle specified"}

            # Use win32gui to resize the window directly
            try:
                import win32gui
                import win32con
            except ImportError:
                return {"success": False, "error": "pywin32 not available. Install with: pip install pywin32"}

            if width is None or height is None or width <= 0 or height <= 0:
                return {"success": False, "error": "Window width and height must be positive"}

            rect = win32gui.GetWindowRect(hwnd)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, rect[0], rect[1], width, height, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
            return {"success": True, "handle": hwnd, "width": width, "height": height}

        except Exception as e:
            logger.error(f"Error resizing window: {e}")
            return {"success": False, "error": str(e)}

    def list_windows(self) -> dict[str, Any]:
        """List all visible windows."""
        if not PYWINAUTO_AVAILABLE:
            return {"success": False, "error": "pywinauto not available"}

        try:
            windows = Desktop(backend="uia").windows()
            result = []
            for w in windows:
                try:
                    if w.is_visible():
                        rect = w.rectangle()
                        # Some windows don't support is_minimized/is_maximized
                        try:
                            is_minimized = w.is_minimized()
                        except Exception:
                            is_minimized = False
                        try:
                            is_maximized = w.is_maximized()
                        except Exception:
                            is_maximized = False

                        result.append(WindowInfo(
                            handle=w.handle,
                            title=w.window_text(),
                            class_name=w.class_name(),
                            process_id=w.process_id(),
                            rectangle={"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom},
                            is_visible=w.is_visible(),
                            is_minimized=is_minimized,
                            is_maximized=is_maximized,
                        ).to_dict())
                except Exception as e:
                    # Skip windows that can't be queried
                    logger.debug(f"Skipping window {w.handle}: {e}")
                    continue

            return {"success": True, "windows": result}

        except Exception as e:
            logger.error(f"Error listing windows: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """Get automation status."""
        return {
            "pywinauto_available": PYWINAUTO_AVAILABLE,
            "tesseract_available": TESSERACT_AVAILABLE,
            "pyautogui_available": PYAUTOGUI_AVAILABLE,
            "ocr_enabled": self.ocr_enabled,
            "current_window": self._window_handle,
        }

    def close(self):
        """Cleanup resources."""
        self._current_window = None
        self._window_handle = None
        self._app = None


# Convenience functions for skill integration
_desktop_automation: Optional[DesktopAutomation] = None


def get_desktop_automation(ocr_enabled: bool = False) -> DesktopAutomation:
    """Get or create the global desktop automation instance."""
    global _desktop_automation
    if _desktop_automation is None:
        _desktop_automation = DesktopAutomation(ocr_enabled=ocr_enabled)
    return _desktop_automation


def reset_desktop_automation():
    """Reset the global desktop automation instance."""
    global _desktop_automation
    if _desktop_automation:
        _desktop_automation.close()
    _desktop_automation = None