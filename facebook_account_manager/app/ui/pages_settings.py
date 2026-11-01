from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.core.config import BACKUP_DIR, DATA_DIR, DB_PATH, KEY_PATH
from app.database.db import Database
from app.ui.widgets import section_title


class SettingsPage(QWidget):
    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        root = QVBoxLayout(self)
        root.addWidget(section_title("Settings & security"))
        root.addWidget(QLabel(f"Data directory: {DATA_DIR}"))
        root.addWidget(QLabel(f"Database: {DB_PATH}"))
        root.addWidget(QLabel(f"Encryption key: {KEY_PATH} (mode 600 when possible)"))
        root.addWidget(QLabel(f"Backups: {BACKUP_DIR}"))
        root.addWidget(
            QLabel(
                "Sessions are encrypted with Fernet. Passwords are never requested or stored.\n"
                "Full cookie values are not shown in the UI or written to logs."
            )
        )
        btn = QPushButton("Create database backup")
        btn.setObjectName("primary")
        btn.clicked.connect(self.backup)
        root.addWidget(btn)
        root.addStretch()

    def backup(self) -> None:
        path = self.db.backup()
        QMessageBox.information(self, "Backup", f"Saved to:\n{path}")
