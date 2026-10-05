"""Real-time DNS & MX Record Validator using dnspython or socket fallback.
Protects sender reputation by verifying target domain can accept mail.
"""

from __future__ import annotations

import logging
import re
import socket
from typing import Optional, Tuple

logger = logging.getLogger("alpha_lead_engine.auditor.dns")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)$")


class SyntaxAndMXValidator:
    """Validates email syntax and real-time domain MX mail exchange capability."""

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self._mx_cache: dict[str, bool] = {}

    def validate_email(self, email: Optional[str]) -> Tuple[bool, str]:
        """Validates email syntax and confirms that target domain has active MX records.
        Returns: (is_valid, reason)
        """
        if not email:
            return False, "No email address provided"

        email = email.strip()
        match = EMAIL_REGEX.match(email)
        if not match:
            return False, "Invalid email address syntax"

        domain = match.group(1).lower().rstrip(".")

        # Check in-memory cache
        if domain in self._mx_cache:
            is_valid = self._mx_cache[domain]
            return is_valid, "Cached MX verification result" if is_valid else "Cached failed MX record"

        # Check disposable / dummy domains
        disposable_domains = {"example.com", "example.org", "example.net", "test.com", "mailinator.com", "tempmail.com"}
        if domain in disposable_domains:
            self._mx_cache[domain] = False
            return False, f"Domain {domain} is reserved or disposable"

        # Check DNS MX records
        has_mx = self._check_mx_records(domain)
        self._mx_cache[domain] = has_mx

        if has_mx:
            return True, f"Domain {domain} has verified active mail servers (MX)"
        else:
            return False, f"Domain {domain} does not have valid MX records to receive mail"

    def _check_mx_records(self, domain: str) -> bool:
        """Query DNS server for MX records, fallback to socket A record lookup."""
        try:
            import dns.resolver

            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout

            answers = resolver.resolve(domain, "MX")
            if answers and len(answers) > 0:
                logger.debug(f"MX lookup succeeded for {domain}: {[str(r.exchange) for r in answers]}")
                return True
        except ImportError:
            logger.debug("dnspython not installed, using socket fallback...")
        except Exception as e:
            logger.debug(f"DNS MX resolution failed for {domain}: {e}")

        # Fallback: check if host domain resolves to an IP address
        try:
            socket.setdefaulttimeout(self.timeout)
            socket.gethostbyname(domain)
            return True
        except Exception:
            return False
