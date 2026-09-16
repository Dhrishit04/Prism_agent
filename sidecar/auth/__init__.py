"""Google OAuth authentication module for Prism."""

from .google_oauth import GoogleOAuthManager, get_google_oauth_manager

__all__ = [
    "GoogleOAuthManager",
    "get_google_oauth_manager",
]