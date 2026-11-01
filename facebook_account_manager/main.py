#!/usr/bin/env python3
"""Facebook Account Manager — entry point."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.core.logging_setup import setup_logging
from app.ui.main_window import MainWindow


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Facebook Account Manager")
    app.setOrganizationName("FAM")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
