"""Logging — never write cookies or tokens."""
from __future__ import annotations

import logging
import re
from pathlib import Path

from app.core.config import LOG_DIR

_SENSITIVE = re.compile(
    r"(c_user|xs|fr|datr|sb|sessionid|access_token|cookie)[=:\s]+[^\s,;\"']+",
    re.IGNORECASE,
)


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _SENSITIVE.sub(r"\1=[REDACTED]", record.msg)
        if record.args:
            record.args = tuple(
                _SENSITIVE.sub(r"\1=[REDACTED]", a) if isinstance(a, str) else a
                for a in record.args
            )
        return True


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("fam")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    fh = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    fh.addFilter(RedactFilter())
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    sh.addFilter(RedactFilter())
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger
