"""Database CRUD and session isolation tests."""
from __future__ import annotations

import os
import tempfile

os.environ["FAM_DATA_DIR"] = tempfile.mkdtemp()

from app.accounts.service import AccountService, mask_cookie_preview  # noqa: E402
from app.database.db import Database  # noqa: E402
from app.database.models import Account, ContentDraft, ScheduledTask  # noqa: E402


def test_account_crud_and_session():
    db = Database()
    svc = AccountService(db)
    session = '[{"name":"c_user","value":"111"},{"name":"xs","value":"abc"}]'
    aid = svc.create("TestNick", profile_id="999", session_json=session)
    acc = db.get_account(aid)
    assert acc is not None
    assert acc.nickname == "TestNick"
    assert acc.has_session is True
    loaded = db.get_session(aid)
    assert loaded is not None
    assert "c_user" in loaded
    # UI mask must not leak value
    preview = mask_cookie_preview(loaded)
    assert "abc" not in preview
    assert "secret" not in preview.lower()

    svc.clear_session(aid)
    assert db.get_session(aid) is None
    acc2 = db.get_account(aid)
    assert acc2 is not None
    assert acc2.has_session is False

    svc.delete(aid)
    assert db.get_account(aid) is None


def test_import_json_and_delete(tmp_path):
    db = Database()
    svc = AccountService(db)
    path = tmp_path / "acc.json"
    path.write_text(
        '[{"nickname":"A1","profile_id":"1"},{"nickname":"A2","tags":"work"}]',
        encoding="utf-8",
    )
    ok, errors = svc.import_json(path)
    assert ok == 2
    assert errors == []
    accounts = db.list_accounts()
    assert len(accounts) >= 2
    for a in accounts:
        if a.nickname in ("A1", "A2"):
            svc.delete(a.id)


def test_drafts_and_tasks():
    db = Database()
    did = db.add_draft(ContentDraft(title="Hello", body="World", status="Draft"))
    drafts = db.list_drafts()
    assert any(d.id == did for d in drafts)
    db.delete_draft(did)
    tid = db.add_task(ScheduledTask(title="Remind post", due_at="2099-01-01 00:00:00"))
    tasks = db.list_tasks(pending_only=True)
    assert any(t.id == tid for t in tasks)
    db.delete_task(tid)


def test_backup():
    db = Database()
    path = db.backup()
    assert path.exists()
    assert path.stat().st_size > 0
