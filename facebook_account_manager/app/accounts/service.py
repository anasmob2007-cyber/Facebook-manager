"""Account import/export and management helpers."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Optional

from app.database.db import Database
from app.database.models import Account, AccountStatus


ALLOWED_COOKIE_KEYS = {
    "c_user",
    "xs",
    "fr",
    "datr",
    "sb",
    "wd",
    "presence",
}


def mask_cookie_preview(session_json: Optional[str]) -> str:
    """Never show full cookie values — only key names + presence."""
    if not session_json:
        return "(no session)"
    try:
        data = json.loads(session_json)
        if isinstance(data, list):
            names = [c.get("name", "?") for c in data if isinstance(c, dict)]
            return f"{len(names)} cookies: " + ", ".join(names[:8]) + ("…" if len(names) > 8 else "")
        if isinstance(data, dict):
            return "keys: " + ", ".join(list(data.keys())[:8])
    except (json.JSONDecodeError, TypeError):
        return "(invalid session data)"
    return "(session present)"


class AccountService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(
        self,
        nickname: str,
        profile_id: str = "",
        group_name: str = "Default",
        tags: str = "",
        notes: str = "",
        session_json: Optional[str] = None,
    ) -> int:
        if not nickname.strip():
            raise ValueError("Nickname is required")
        if session_json:
            self._validate_session_payload(session_json)
        acc = Account(
            nickname=nickname.strip(),
            profile_id=profile_id.strip(),
            group_name=group_name.strip() or "Default",
            tags=tags.strip(),
            notes=notes.strip(),
            status=AccountStatus.ACTIVE.value if session_json else AccountStatus.REQUIRES_LOGIN.value,
        )
        return self.db.add_account(acc, session_json)

    def update(self, acc: Account) -> None:
        if not acc.nickname.strip():
            raise ValueError("Nickname is required")
        self.db.update_account(acc)

    def delete(self, account_id: int) -> None:
        self.db.delete_account(account_id)

    def clear_session(self, account_id: int) -> None:
        self.db.clear_session(account_id)

    def set_session(self, account_id: int, session_json: str) -> None:
        self._validate_session_payload(session_json)
        self.db.set_session(account_id, session_json)

    def _validate_session_payload(self, session_json: str) -> None:
        try:
            data = json.loads(session_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON session data: {e}") from e
        if not isinstance(data, (list, dict)):
            raise ValueError("Session must be a JSON object or array of cookies")
        # Soft check — user-provided only; we do not fetch cookies ourselves
        if isinstance(data, list) and len(data) == 0:
            raise ValueError("Cookie list is empty")

    def import_json(self, path: Path) -> tuple[int, list[str]]:
        """Import accounts from JSON. Expected: list of objects with nickname, optional fields."""
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("accounts", [data])
        if not isinstance(data, list):
            raise ValueError("JSON must be a list of accounts")
        ok, errors = 0, []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f"row {i}: not an object")
                continue
            try:
                session = item.get("session") or item.get("cookies")
                if session is not None and not isinstance(session, str):
                    session = json.dumps(session)
                self.create(
                    nickname=str(item.get("nickname") or item.get("name") or "").strip(),
                    profile_id=str(item.get("profile_id") or item.get("id") or ""),
                    group_name=str(item.get("group") or item.get("group_name") or "Default"),
                    tags=str(item.get("tags") or ""),
                    notes=str(item.get("notes") or ""),
                    session_json=session,
                )
                ok += 1
            except Exception as e:
                errors.append(f"row {i}: {e}")
        return ok, errors

    def import_csv(self, path: Path) -> tuple[int, list[str]]:
        ok, errors = 0, []
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV has no header")
            for i, row in enumerate(reader):
                try:
                    nick = (row.get("nickname") or row.get("name") or "").strip()
                    session = (row.get("session") or row.get("cookies") or "").strip() or None
                    self.create(
                        nickname=nick,
                        profile_id=(row.get("profile_id") or row.get("id") or "").strip(),
                        group_name=(row.get("group") or row.get("group_name") or "Default").strip(),
                        tags=(row.get("tags") or "").strip(),
                        notes=(row.get("notes") or "").strip(),
                        session_json=session,
                    )
                    ok += 1
                except Exception as e:
                    errors.append(f"row {i + 2}: {e}")
        return ok, errors

    def export_json(self, path: Path) -> int:
        accounts = self.db.list_accounts()
        payload = []
        for a in accounts:
            payload.append(
                {
                    "nickname": a.nickname,
                    "profile_id": a.profile_id,
                    "group": a.group_name,
                    "tags": a.tags,
                    "notes": a.notes,
                    "status": a.status,
                    # session intentionally omitted from export for safety
                }
            )
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return len(payload)
