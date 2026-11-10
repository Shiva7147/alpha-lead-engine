"""Email Sender Module - Dispatches MIME messages with proper threading headers via Gmail API or dry-run simulator.
"""

from __future__ import annotations

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from typing import Dict, Optional, Tuple

from alpha_lead_engine.automation.gmail_oauth import GmailOAuthManager

logger = logging.getLogger("alpha_lead_engine.automation.sender")


class EmailSender:
    """Sends cold emails and threaded follow-ups with RFC-compliant headers."""

    def __init__(self, oauth_manager: Optional[GmailOAuthManager] = None, dry_run: bool = False):
        self.oauth_manager = oauth_manager or GmailOAuthManager()
        self.dry_run = dry_run
        self.service = None if dry_run else self.oauth_manager.get_gmail_service()

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        sender_email: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Sends an email via Gmail API or simulates in dry-run mode.
        Returns: (success, thread_id, message_id)
        """
        if self.dry_run or not self.service:
            logger.info(f"[DRY RUN / SIMULATION] Sending email to {to_email} | Subject: '{subject}'")
            fake_thread = thread_id or f"mock_thread_{hash(to_email) % 100000}"
            fake_msg_id = f"mock_msg_{hash(subject) % 100000}"
            return True, fake_thread, fake_msg_id

        try:
            message = MIMEMultipart("alternative")
            message["to"] = to_email
            message["subject"] = subject
            if sender_email:
                message["from"] = sender_email

            if in_reply_to:
                message["In-Reply-To"] = in_reply_to
                message["References"] = in_reply_to

            # Plain text part
            text_part = MIMEText(body, "plain", "utf-8")
            message.attach(text_part)

            raw_string = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            body_payload: Dict[str, str] = {"raw": raw_string}

            if thread_id:
                body_payload["threadId"] = thread_id

            logger.info(f"Dispatching message via Gmail API to {to_email}...")
            sent_msg = self.service.users().messages().send(userId="me", body=body_payload).execute()
            
            res_thread_id = sent_msg.get("threadId")
            res_msg_id = sent_msg.get("id")

            logger.info(f"Email successfully sent! Message ID: {res_msg_id}, Thread ID: {res_thread_id}")
            return True, res_thread_id, res_msg_id

        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via Gmail API: {e}")
            return False, None, None
