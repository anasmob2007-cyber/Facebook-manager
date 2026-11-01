"""Encryption round-trip tests."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Isolate key file for tests
_tmp = tempfile.mkdtemp()
os.environ["FAM_DATA_DIR"] = _tmp

from app.security.crypto import decrypt_text, encrypt_text  # noqa: E402


def test_encrypt_decrypt_roundtrip():
    plain = '{"cookies":[{"name":"c_user","value":"secret123"}]}'
    token = encrypt_text(plain)
    assert token != plain.encode()
    assert decrypt_text(token) == plain


def test_different_plaintexts_differ():
    a = encrypt_text("alpha")
    b = encrypt_text("beta")
    assert a != b
