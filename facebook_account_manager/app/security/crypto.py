"""Local encryption for session cookie blobs. Fernet + key file with restricted perms."""
from __future__ import annotations

import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import KEY_PATH


def _ensure_key() -> bytes:
    if KEY_PATH.exists():
        return KEY_PATH.read_bytes()
    key = Fernet.generate_key()
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    KEY_PATH.write_bytes(key)
    try:
        os.chmod(KEY_PATH, 0o600)
    except OSError:
        pass
    return key


def get_fernet() -> Fernet:
    return Fernet(_ensure_key())


def encrypt_bytes(plain: bytes) -> bytes:
    return get_fernet().encrypt(plain)


def decrypt_bytes(token: bytes) -> bytes:
    try:
        return get_fernet().decrypt(token)
    except InvalidToken as e:
        raise ValueError("Cannot decrypt session data — key mismatch or corrupted") from e


def encrypt_text(plain: str) -> bytes:
    return encrypt_bytes(plain.encode("utf-8"))


def decrypt_text(token: bytes) -> str:
    return decrypt_bytes(token).decode("utf-8")
