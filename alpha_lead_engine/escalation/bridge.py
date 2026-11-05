"""Mobile & Multi-Channel Human Escalation Bridge.
Allows a sales operator to receive real-time push alerts on their phone (Telegram, NTFY, or Webhook)
and review/approve decisions directly from mobile or interactive terminal.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from alpha_lead_engine.auditor.schemas import HumanReviewCheckpoint

logger = logging.getLogger("alpha_lead_engine.escalation.bridge")


class MobileEscalationBridge:
    """Dispatches human escalation notifications to the operator's mobile device.
    Supported channels:
    1. ntfy.sh (Zero-config instant push notifications to Android & iOS app)
    2. Telegram Bot API
    3. Custom Webhook (Slack, Discord, Zapier)
    4. Terminal Interactive fallback
    """

    def __init__(
        self,
        ntfy_topic: Optional[str] = None,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ):
        self.ntfy_topic = ntfy_topic or os.getenv("NTFY_TOPIC", "alpha_lead_engine_alerts")
        self.telegram_bot_token = telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.webhook_url = webhook_url or os.getenv("ESCALATION_WEBHOOK_URL")

    def dispatch_alert(self, checkpoint: HumanReviewCheckpoint, lead_name: str, lead_email: Optional[str] = None) -> bool:
        """Sends instant notification to operator's mobile phone."""
        title = f"🚨 Lead Escalation: {lead_name}"
        message = (
            f"Business: {lead_name} ({lead_email or 'No email'})\n"
            f"Reason: {checkpoint.reason}\n"
            f"Action: {checkpoint.proposed_action}\n"
            f"Checkpoint ID: {checkpoint.checkpoint_id}"
        )

        success = False

        # Channel 1: ntfy.sh (Free, open source push notifications for iOS & Android)
        if self.ntfy_topic:
            try:
                ntfy_url = f"https://ntfy.sh/{self.ntfy_topic}"
                req = urllib.request.Request(
                    ntfy_url,
                    data=message.encode("utf-8"),
                    headers={
                        "Title": title,
                        "Priority": "high",
                        "Tags": "rotating_light,briefcase",
                        "Actions": f"view, Open Pipeline, http://localhost:8501, clear=true",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        logger.info(f"Mobile push notification sent via ntfy.sh topic: {self.ntfy_topic}")
                        success = True
            except Exception as e:
                logger.debug(f"ntfy alert failed: {e}")

        # Channel 2: Telegram Bot
        if self.telegram_bot_token and self.telegram_chat_id:
            try:
                tg_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                payload = json.dumps({
                    "chat_id": self.telegram_chat_id,
                    "text": f"*{title}*\n\n{message}",
                    "parse_mode": "Markdown",
                }).encode("utf-8")
                req = urllib.request.Request(tg_url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        logger.info("Mobile notification sent to Telegram.")
                        success = True
            except Exception as e:
                logger.debug(f"Telegram notification failed: {e}")

        # Channel 3: Custom Webhook
        if self.webhook_url:
            try:
                payload = json.dumps({
                    "title": title,
                    "text": message,
                    "checkpoint": checkpoint.model_dump(),
                }).encode("utf-8")
                req = urllib.request.Request(self.webhook_url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in (200, 201, 204):
                        logger.info("Notification sent to custom webhook.")
                        success = True
            except Exception as e:
                logger.debug(f"Webhook dispatch failed: {e}")

        return success
