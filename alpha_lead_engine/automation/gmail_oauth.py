"""Google OAuth 2.0 Flow Manager for Gmail API authentication.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("alpha_lead_engine.automation.oauth")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
]


class GmailOAuthManager:
    """Handles Google OAuth credentials, token persistence, and API service construction."""

    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)

    @property
    def has_credentials(self) -> bool:
        return self.credentials_path.exists()

    @property
    def is_authenticated(self) -> bool:
        return self.token_path.exists()

    def authenticate(self) -> bool:
        """Runs the interactive browser OAuth flow and saves token.json."""
        if not self.has_credentials:
            logger.warning(
                f"OAuth credentials file not found at '{self.credentials_path}'. "
                "Download your OAuth client ID credentials from Google Cloud Console."
            )
            return False

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow

            creds = None
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired Google OAuth token...")
                    creds.refresh(Request())
                else:
                    logger.info("Launching local browser for Google OAuth authorization...")
                    flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)

                with open(self.token_path, "w") as token_file:
                    token_file.write(creds.to_json())
                logger.info(f"OAuth credentials successfully saved to '{self.token_path}'.")

            return True

        except Exception as e:
            logger.error(f"OAuth authentication error: {e}")
            return False

    def get_gmail_service(self):
        """Constructs authenticated Google API client service for Gmail."""
        if not self.is_authenticated:
            logger.info("Token not found, attempting authentication flow...")
            if not self.authenticate():
                return None

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            service = build("gmail", "v1", credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Failed building Gmail service: {e}")
            return None
