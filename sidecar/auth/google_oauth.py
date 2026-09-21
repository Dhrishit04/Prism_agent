"""Google OAuth 2.0 authentication manager for Tesseract.

Handles OAuth flow, token storage with AES-256 encryption, and refresh token flow.
"""

import base64
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

logger = logging.getLogger(__name__)

# OAuth 2.0 scopes for Gmail and Calendar
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]
ALL_SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES

# Redirect URI for local callback
REDIRECT_URI = "http://localhost:8765/oauth/callback"

# Token storage path
TOKENS_DIR = Path.home() / ".tesseract" / "tokens"
TOKEN_FILE = TOKENS_DIR / "google_tokens.enc"
KEY_FILE = TOKENS_DIR / "encryption_key"


@dataclass
class OAuthStatus:
    """Status of Google OAuth connection."""
    connected: bool
    email: Optional[str] = None
    scopes: list[str] = None
    expires_at: Optional[float] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []


class GoogleOAuthManager:
    """Manages Google OAuth 2.0 authentication for Tesseract."""

    def __init__(self):
        self._credentials: Optional[Credentials] = None
        self._client_id: Optional[str] = None
        self._client_secret: Optional[str] = None
        self._fernet: Optional[Fernet] = None
        self._initialized = False

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create the encryption key for token storage."""
        TOKENS_DIR.mkdir(parents=True, exist_ok=True)

        if KEY_FILE.exists():
            key = KEY_FILE.read_bytes()
        else:
            key = Fernet.generate_key()
            KEY_FILE.write_bytes(key)
            # Restrict permissions on Windows (best effort)
            try:
                os.chmod(KEY_FILE, 0o600)
            except Exception:
                pass
        return key

    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance for encryption."""
        if self._fernet is None:
            key = self._get_or_create_encryption_key()
            self._fernet = Fernet(key)
        return self._fernet

    def configure(self, client_id: str, client_secret: str) -> None:
        """Configure OAuth client credentials.

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._initialized = True

    def is_configured(self) -> bool:
        """Check if OAuth client is configured."""
        return self._initialized and self._client_id is not None and self._client_secret is not None

    def load_settings(self, settings: dict) -> None:
        """Load OAuth settings from settings dict.

        Args:
            settings: Full settings dict from settings.json
        """
        google_settings = settings.get("google", {})
        client_id = google_settings.get("client_id", "")
        client_secret = google_settings.get("client_secret", "")
        if client_id and client_secret:
            self.configure(client_id, client_secret)

    def get_authorization_url(self) -> str:
        """Get the Google OAuth authorization URL.

        Returns:
            Authorization URL to open in browser

        Raises:
            ValueError: If OAuth client not configured
        """
        if not self.is_configured():
            raise ValueError("Google OAuth not configured. Set client_id and client_secret in settings.")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uris": [REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=ALL_SCOPES,
            redirect_uri=REDIRECT_URI,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",  # Force consent to get refresh token
        )
        return auth_url

    async def handle_callback(self, code: str) -> OAuthStatus:
        """Handle OAuth callback and exchange code for tokens.

        Args:
            code: Authorization code from Google redirect

        Returns:
            OAuthStatus with connection info
        """
        if not self.is_configured():
            return OAuthStatus(connected=False, error="Google OAuth not configured")

        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "redirect_uris": [REDIRECT_URI],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=ALL_SCOPES,
                redirect_uri=REDIRECT_URI,
            )
            flow.fetch_token(code=code)
            self._credentials = flow.credentials

            # Save encrypted tokens
            await self._save_credentials()

            # Get user email
            email = await self._get_user_email()

            return OAuthStatus(
                connected=True,
                email=email,
                scopes=list(self._credentials.scopes) if self._credentials.scopes else [],
                expires_at=self._credentials.expiry.timestamp() if self._credentials.expiry else None,
            )
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return OAuthStatus(connected=False, error=str(e))

    async def _save_credentials(self) -> None:
        """Save credentials to encrypted file."""
        if not self._credentials:
            return

        token_data = {
            "token": self._credentials.token,
            "refresh_token": self._credentials.refresh_token,
            "token_uri": self._credentials.token_uri,
            "client_id": self._credentials.client_id,
            "client_secret": self._credentials.client_secret,
            "scopes": list(self._credentials.scopes) if self._credentials.scopes else [],
            "expiry": self._credentials.expiry.isoformat() if self._credentials.expiry else None,
        }

        fernet = self._get_fernet()
        encrypted = fernet.encrypt(json.dumps(token_data).encode())
        TOKEN_FILE.write_bytes(encrypted)

    async def load_credentials(self) -> bool:
        """Load credentials from encrypted file.

        Returns:
            True if credentials loaded successfully
        """
        if not TOKEN_FILE.exists():
            return False

        try:
            fernet = self._get_fernet()
            encrypted = TOKEN_FILE.read_bytes()
            token_data = json.loads(fernet.decrypt(encrypted).decode())

            self._credentials = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=token_data.get("scopes"),
            )

            # Parse expiry if present
            if token_data.get("expiry"):
                from datetime import datetime
                self._credentials.expiry = datetime.fromisoformat(token_data["expiry"])

            # Refresh if expired
            if self._credentials.expired and self._credentials.refresh_token:
                await self._refresh_credentials()

            return self._credentials is not None and self._credentials.valid
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return False

    async def _refresh_credentials(self) -> bool:
        """Refresh expired access token using refresh token.

        Returns:
            True if refresh successful
        """
        if not self._credentials or not self._credentials.refresh_token:
            return False

        try:
            self._credentials.refresh(Request())
            await self._save_credentials()
            return True
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return False

    async def _get_user_email(self) -> Optional[str]:
        """Get the authenticated user's email address."""
        if not self._credentials or not self._credentials.valid:
            return None

        try:
            from googleapiclient.discovery import build
            service = build("oauth2", "v2", credentials=self._credentials)
            user_info = service.userinfo().get().execute()
            return user_info.get("email")
        except Exception as e:
            logger.error(f"Failed to get user email: {e}")
            return None

    def get_credentials(self) -> Optional[Credentials]:
        """Get valid credentials, refreshing if needed.

        Returns:
            Valid Credentials object or None
        """
        if not self._credentials:
            return None

        if self._credentials.expired and self._credentials.refresh_token:
            import asyncio
            asyncio.create_task(self._refresh_credentials())

        return self._credentials if self._credentials.valid else None

    async def get_status(self) -> OAuthStatus:
        """Get current OAuth connection status."""
        if not self.is_configured():
            return OAuthStatus(connected=False, error="Not configured")

        # Try to load saved credentials
        if self._credentials is None:
            await self.load_credentials()

        if self._credentials and self._credentials.valid:
            email = await self._get_user_email()
            return OAuthStatus(
                connected=True,
                email=email,
                scopes=list(self._credentials.scopes) if self._credentials.scopes else [],
                expires_at=self._credentials.expiry.timestamp() if self._credentials.expiry else None,
            )
        elif self._credentials:
            # Has credentials but expired and no refresh token
            return OAuthStatus(
                connected=False,
                error="Token expired, re-authentication required",
            )
        else:
            return OAuthStatus(connected=False, error="Not authenticated")

    async def disconnect(self) -> OAuthStatus:
        """Disconnect and remove stored tokens."""
        self._credentials = None
        try:
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
            if KEY_FILE.exists():
                KEY_FILE.unlink()
            return OAuthStatus(connected=False, error="Disconnected")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            return OAuthStatus(connected=False, error=str(e))

    def get_gmail_service(self):
        """Get authenticated Gmail API service."""
        creds = self.get_credentials()
        if not creds:
            raise ValueError("No valid credentials. Run OAuth flow first.")
        from googleapiclient.discovery import build
        return build("gmail", "v1", credentials=creds)

    def get_calendar_service(self):
        """Get authenticated Calendar API service."""
        creds = self.get_credentials()
        if not creds:
            raise ValueError("No valid credentials. Run OAuth flow first.")
        from googleapiclient.discovery import build
        return build("calendar", "v3", credentials=creds)


# Global instance
_oauth_manager: Optional[GoogleOAuthManager] = None


def get_google_oauth_manager() -> GoogleOAuthManager:
    """Get the global Google OAuth manager instance."""
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = GoogleOAuthManager()
    return _oauth_manager


def reset_oauth_manager() -> None:
    """Reset the global OAuth manager (useful for testing)."""
    global _oauth_manager
    _oauth_manager = None