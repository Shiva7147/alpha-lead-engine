"""Pipeline Store - SQLite-backed persistent state store for all leads, audits, and outreach sequences.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from alpha_lead_engine.auditor.schemas import CampaignState, EnrichedLead, LeadStatus

logger = logging.getLogger("alpha_lead_engine.auditor.store")


class PipelineStore:
    """Manages persistent lead storage, state transitions, and campaign analytics via SQLite."""

    def __init__(self, db_path: str = "alpha_leads.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                clean_domain TEXT,
                business_name TEXT,
                email TEXT,
                status TEXT,
                mx_valid INTEGER,
                score INTEGER,
                fit_tier TEXT,
                followup_1_sent_at TEXT,
                followup_2_sent_at TEXT,
                lead_data TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_domain ON leads (clean_domain)")
            conn.commit()

    def save_lead(self, lead: EnrichedLead):
        """Upserts an enriched lead into the database."""
        now = datetime.utcnow().isoformat()
        score = lead.audit.score if lead.audit else 0
        fit_tier = lead.audit.fit_tier.value if lead.audit else "Unknown"

        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO leads (id, clean_domain, business_name, email, status, mx_valid, score, fit_tier, followup_1_sent_at, followup_2_sent_at, lead_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status=excluded.status,
                mx_valid=excluded.mx_valid,
                score=excluded.score,
                fit_tier=excluded.fit_tier,
                followup_1_sent_at=excluded.followup_1_sent_at,
                followup_2_sent_at=excluded.followup_2_sent_at,
                lead_data=excluded.lead_data,
                updated_at=excluded.updated_at
            """, (
                lead.id,
                lead.clean_domain,
                lead.raw.business_name,
                lead.raw.email,
                lead.status.value,
                1 if lead.mx_valid else 0,
                score,
                fit_tier,
                lead.followup_1_sent_at.isoformat() if lead.followup_1_sent_at else None,
                lead.followup_2_sent_at.isoformat() if lead.followup_2_sent_at else None,
                lead.model_dump_json(),
                lead.created_at.isoformat(),
                now
            ))
            conn.commit()

    def get_lead(self, lead_id: str) -> Optional[EnrichedLead]:
        """Retrieves a single lead by its unique ID."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT lead_data FROM leads WHERE id = ?", (lead_id,))
            row = cur.fetchone()
            if row:
                return EnrichedLead.model_validate_json(row["lead_data"])
        return None

    def list_leads(self, status: Optional[LeadStatus] = None, limit: int = 100) -> List[EnrichedLead]:
        """Lists stored leads, optionally filtered by status."""
        query = "SELECT lead_data FROM leads"
        params: list = []
        if status:
            query += " WHERE status = ?"
            params.append(status.value)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        results: List[EnrichedLead] = []
        with self._get_connection() as conn:
            cur = conn.execute(query, tuple(params))
            for row in cur.fetchall():
                results.append(EnrichedLead.model_validate_json(row["lead_data"]))
        return results

    def update_status(self, lead_id: str, new_status: LeadStatus, **kwargs):
        """Transitions lead to a new state and updates timestamp."""
        lead = self.get_lead(lead_id)
        if not lead:
            return

        lead.status = new_status
        lead.updated_at = datetime.utcnow()
        for k, v in kwargs.items():
            if hasattr(lead, k):
                setattr(lead, k, v)

        self.save_lead(lead)

    def get_campaign_metrics(self, campaign_name: str = "Default Campaign") -> CampaignState:
        """Computes summary statistics for pipeline health reporting."""
        with self._get_connection() as conn:
            total_discovered = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            total_mx_verified = conn.execute("SELECT COUNT(*) FROM leads WHERE mx_valid = 1").fetchone()[0]
            total_audited = conn.execute("SELECT COUNT(*) FROM leads WHERE score > 0").fetchone()[0]
            total_sent = conn.execute("SELECT COUNT(*) FROM leads WHERE status IN ('SENT', 'FOLLOWUP_PENDING', 'REPLIED')").fetchone()[0]
            total_followups_sent = conn.execute("SELECT COUNT(*) FROM leads WHERE followup_1_sent_at IS NOT NULL").fetchone()[0]
            total_replies = conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'REPLIED'").fetchone()[0]
            total_pending_human = conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'NEEDS_HUMAN_REVIEW'").fetchone()[0]

            return CampaignState(
                campaign_name=campaign_name,
                total_discovered=total_discovered,
                total_mx_verified=total_mx_verified,
                total_audited=total_audited,
                total_sent=total_sent,
                total_followups_sent=total_followups_sent,
                total_replies=total_replies,
                total_pending_human_review=total_pending_human,
                updated_at=datetime.utcnow()
            )
