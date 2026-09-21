"""Google OAuth authentication module for Tesseract."""

from .google_oauth import GoogleOAuthManager, get_google_oauth_manager

__all__ = [
    "GoogleOAuthManager",
    "get_google_oauth_manager",
]