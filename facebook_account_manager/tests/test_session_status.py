"""Session expiration / status handling."""
from __future__ import annotations

import os
import tempfile

os.environ["FAM_DATA_DIR"] = tempfile.mkdtemp()

from app.accounts.service import AccountService  # noqa: E402
from app.database.db import Database  # noqa: E402
from app.database.models import AccountStatus  # noqa: E402
from app.scheduler.tasks import HealthChecker  # noqa: E402


def test_requires_login_when_no_session():
    db = Database()
    svc = AccountService(db)
    aid = svc.create("NoSess")
    acc = db.get_account(aid)
    assert acc is not None
    assert acc.status == AccountStatus.REQUIRES_LOGIN.value
    msgs = HealthChecker(db).run()
    assert any("NoSess" in m for m in msgs)
