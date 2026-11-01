"""Safe productivity scheduling — reminders and health checks only."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from app.database.db import Database
from app.database.models import AccountStatus

logger = logging.getLogger("fam.scheduler")


class HealthChecker:
    """
    Local health checks only:
    - Flag accounts with no session
    - Flag very old last_verified timestamps
    Does NOT hit Facebook with artificial engagement.
    """

    def __init__(self, db: Database, stale_days: int = 14) -> None:
        self.db = db
        self.stale_days = stale_days

    def run(self) -> list[str]:
        messages: list[str] = []
        now = datetime.now(timezone.utc)
        for acc in self.db.list_accounts():
            if not acc.has_session:
                if acc.status != AccountStatus.REQUIRES_LOGIN.value:
                    acc.status = AccountStatus.REQUIRES_LOGIN.value
                    self.db.update_account(acc)
                messages.append(f"{acc.nickname}: no session — Requires Login")
                continue
            if acc.last_verified:
                try:
                    lv = datetime.strptime(acc.last_verified, "%Y-%m-%d %H:%M:%S").replace(
                        tzinfo=timezone.utc
                    )
                    age = (now - lv).days
                    if age >= self.stale_days:
                        messages.append(f"{acc.nickname}: last verified {age} days ago")
                except ValueError:
                    pass
        self.db.log_activity(None, "health_check", f"{len(messages)} findings")
        return messages


class ReminderService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def due_tasks(self) -> list[str]:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        out = []
        for t in self.db.list_tasks(pending_only=True):
            if t.due_at and t.due_at <= now:
                out.append(f"[Due] {t.title}" + (f" — {t.description}" if t.description else ""))
        return out
