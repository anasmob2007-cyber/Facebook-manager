"""Application configuration — paths and non-secret defaults."""
from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Facebook Account Manager"
APP_VERSION = "1.0.0"

# Data lives under user home by default (not inside install tree)
_BASE = Path(os.environ.get("FAM_DATA_DIR", Path.home() / ".facebook_account_manager"))
DATA_DIR = _BASE
DB_PATH = DATA_DIR / "accounts.db"
KEY_PATH = DATA_DIR / ".master.key"
BACKUP_DIR = DATA_DIR / "backups"
BROWSER_PROFILES_DIR = DATA_DIR / "browser_profiles"
LOG_DIR = DATA_DIR / "logs"

for _p in (DATA_DIR, BACKUP_DIR, BROWSER_PROFILES_DIR, LOG_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# UI
DARK_BG = "#1a1b1e"
DARK_SURFACE = "#25262b"
DARK_BORDER = "#373a40"
ACCENT = "#4c6ef5"
ACCENT_HOVER = "#5c7cfa"
TEXT = "#e9ecef"
TEXT_MUTED = "#909296"
DANGER = "#fa5252"
SUCCESS = "#40c057"
WARNING = "#fab005"
