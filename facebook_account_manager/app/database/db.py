"""SQLite access layer."""
from __future__ import annotations

import json
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Iterable, Optional

from app.core.config import BACKUP_DIR, DB_PATH
from app.database.models import Account, ActivityLog, ContentDraft, ScheduledTask
from app.security.crypto import decrypt_bytes, encrypt_bytes


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nickname TEXT NOT NULL,
                    profile_id TEXT DEFAULT '',
                    group_name TEXT DEFAULT 'Default',
                    tags TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    status TEXT DEFAULT 'Unknown',
                    last_verified TEXT,
                    last_activity TEXT,
                    session_blob BLOB,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS content_drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    title TEXT DEFAULT '',
                    body TEXT DEFAULT '',
                    media_note TEXT DEFAULT '',
                    status TEXT DEFAULT 'Draft',
                    scheduled_at TEXT,
                    published_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    due_at TEXT,
                    status TEXT DEFAULT 'Pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    action TEXT NOT NULL,
                    detail TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);
                CREATE INDEX IF NOT EXISTS idx_accounts_group ON accounts(group_name);
                CREATE INDEX IF NOT EXISTS idx_drafts_account ON content_drafts(account_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_due ON scheduled_tasks(due_at);
                """
            )

    # ── Accounts ──────────────────────────────────────────────

    def add_account(self, acc: Account, session_json: Optional[str] = None) -> int:
        now = _now()
        blob = encrypt_bytes(session_json.encode("utf-8")) if session_json else None
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO accounts (
                    nickname, profile_id, group_name, tags, notes, status,
                    last_verified, last_activity, session_blob, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    acc.nickname,
                    acc.profile_id,
                    acc.group_name or "Default",
                    acc.tags,
                    acc.notes,
                    acc.status,
                    acc.last_verified,
                    acc.last_activity,
                    blob,
                    now,
                    now,
                ),
            )
            aid = int(cur.lastrowid)
            conn.execute(
                "INSERT INTO activity_logs (account_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
                (aid, "account_created", f"nickname={acc.nickname}", now),
            )
            return aid

    def update_account(self, acc: Account) -> None:
        if not acc.id:
            raise ValueError("account id required")
        now = _now()
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE accounts SET nickname=?, profile_id=?, group_name=?, tags=?, notes=?,
                    status=?, last_verified=?, last_activity=?, updated_at=?
                WHERE id=?
                """,
                (
                    acc.nickname,
                    acc.profile_id,
                    acc.group_name,
                    acc.tags,
                    acc.notes,
                    acc.status,
                    acc.last_verified,
                    acc.last_activity,
                    now,
                    acc.id,
                ),
            )

    def set_session(self, account_id: int, session_json: Optional[str]) -> None:
        blob = encrypt_bytes(session_json.encode("utf-8")) if session_json else None
        now = _now()
        with self.connect() as conn:
            conn.execute(
                "UPDATE accounts SET session_blob=?, updated_at=?, status=? WHERE id=?",
                (
                    blob,
                    now,
                    "Active" if session_json else "Requires Login",
                    account_id,
                ),
            )
            conn.execute(
                "INSERT INTO activity_logs (account_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
                (
                    account_id,
                    "session_updated" if session_json else "session_cleared",
                    "session encrypted" if session_json else "session removed",
                    now,
                ),
            )

    def get_session(self, account_id: int) -> Optional[str]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT session_blob FROM accounts WHERE id=?", (account_id,)
            ).fetchone()
            if not row or row["session_blob"] is None:
                return None
            return decrypt_bytes(row["session_blob"]).decode("utf-8")

    def clear_session(self, account_id: int) -> None:
        self.set_session(account_id, None)

    def delete_account(self, account_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))

    def get_account(self, account_id: int) -> Optional[Account]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
            return self._row_to_account(row) if row else None

    def list_accounts(
        self,
        status: Optional[str] = None,
        group: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[Account]:
        sql = "SELECT * FROM accounts WHERE 1=1"
        params: list[Any] = []
        if status:
            sql += " AND status=?"
            params.append(status)
        if group:
            sql += " AND group_name=?"
            params.append(group)
        if search:
            sql += " AND (nickname LIKE ? OR profile_id LIKE ? OR tags LIKE ? OR notes LIKE ?)"
            q = f"%{search}%"
            params.extend([q, q, q, q])
        sql += " ORDER BY nickname COLLATE NOCASE"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_account(r) for r in rows]

    def _row_to_account(self, row: sqlite3.Row) -> Account:
        return Account(
            id=row["id"],
            nickname=row["nickname"],
            profile_id=row["profile_id"] or "",
            group_name=row["group_name"] or "Default",
            tags=row["tags"] or "",
            notes=row["notes"] or "",
            status=row["status"] or "Unknown",
            last_verified=row["last_verified"],
            last_activity=row["last_activity"],
            has_session=row["session_blob"] is not None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ── Content ───────────────────────────────────────────────

    def add_draft(self, d: ContentDraft) -> int:
        now = _now()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO content_drafts (
                    account_id, title, body, media_note, status, scheduled_at, published_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    d.account_id,
                    d.title,
                    d.body,
                    d.media_note,
                    d.status,
                    d.scheduled_at,
                    d.published_at,
                    now,
                    now,
                ),
            )
            return int(cur.lastrowid)

    def update_draft(self, d: ContentDraft) -> None:
        if not d.id:
            raise ValueError("draft id required")
        now = _now()
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE content_drafts SET account_id=?, title=?, body=?, media_note=?,
                    status=?, scheduled_at=?, published_at=?, updated_at=? WHERE id=?
                """,
                (
                    d.account_id,
                    d.title,
                    d.body,
                    d.media_note,
                    d.status,
                    d.scheduled_at,
                    d.published_at,
                    now,
                    d.id,
                ),
            )

    def delete_draft(self, draft_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM content_drafts WHERE id=?", (draft_id,))

    def list_drafts(self, account_id: Optional[int] = None) -> list[ContentDraft]:
        sql = "SELECT * FROM content_drafts"
        params: list[Any] = []
        if account_id is not None:
            sql += " WHERE account_id=?"
            params.append(account_id)
        sql += " ORDER BY updated_at DESC"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_draft(r) for r in rows]

    def _row_to_draft(self, row: sqlite3.Row) -> ContentDraft:
        return ContentDraft(
            id=row["id"],
            account_id=row["account_id"],
            title=row["title"] or "",
            body=row["body"] or "",
            media_note=row["media_note"] or "",
            status=row["status"] or "Draft",
            scheduled_at=row["scheduled_at"],
            published_at=row["published_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ── Tasks ─────────────────────────────────────────────────

    def add_task(self, t: ScheduledTask) -> int:
        now = _now()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO scheduled_tasks (account_id, title, description, due_at, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (t.account_id, t.title, t.description, t.due_at, t.status, now),
            )
            return int(cur.lastrowid)

    def update_task(self, t: ScheduledTask) -> None:
        if not t.id:
            raise ValueError("task id required")
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE scheduled_tasks SET account_id=?, title=?, description=?, due_at=?, status=?
                WHERE id=?
                """,
                (t.account_id, t.title, t.description, t.due_at, t.status, t.id),
            )

    def delete_task(self, task_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM scheduled_tasks WHERE id=?", (task_id,))

    def list_tasks(self, pending_only: bool = False) -> list[ScheduledTask]:
        sql = "SELECT * FROM scheduled_tasks"
        if pending_only:
            sql += " WHERE status='Pending'"
        sql += " ORDER BY due_at IS NULL, due_at ASC"
        with self.connect() as conn:
            rows = conn.execute(sql).fetchall()
            return [
                ScheduledTask(
                    id=r["id"],
                    account_id=r["account_id"],
                    title=r["title"],
                    description=r["description"] or "",
                    due_at=r["due_at"],
                    status=r["status"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # ── Activity ──────────────────────────────────────────────

    def log_activity(self, account_id: Optional[int], action: str, detail: str = "") -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO activity_logs (account_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
                (account_id, action, detail, _now()),
            )

    def list_activity(self, limit: int = 200, account_id: Optional[int] = None) -> list[ActivityLog]:
        sql = "SELECT * FROM activity_logs"
        params: list[Any] = []
        if account_id is not None:
            sql += " WHERE account_id=?"
            params.append(account_id)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [
                ActivityLog(
                    id=r["id"],
                    account_id=r["account_id"],
                    action=r["action"],
                    detail=r["detail"] or "",
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # ── Backup ────────────────────────────────────────────────

    def backup(self) -> Path:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = BACKUP_DIR / f"accounts_{stamp}.db"
        shutil.copy2(self.path, dest)
        return dest

    def stats(self) -> dict[str, int]:
        with self.connect() as conn:
            accounts = conn.execute("SELECT COUNT(*) c FROM accounts").fetchone()["c"]
            active = conn.execute(
                "SELECT COUNT(*) c FROM accounts WHERE status='Active'"
            ).fetchone()["c"]
            drafts = conn.execute("SELECT COUNT(*) c FROM content_drafts").fetchone()["c"]
            tasks = conn.execute(
                "SELECT COUNT(*) c FROM scheduled_tasks WHERE status='Pending'"
            ).fetchone()["c"]
            return {
                "accounts": accounts,
                "active": active,
                "drafts": drafts,
                "pending_tasks": tasks,
            }
