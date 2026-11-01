from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from app.database.db import Database
from app.ui.widgets import section_title, stat_card


class DashboardPage(QWidget):
    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self._build()

    def _build(self) -> None:
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(section_title("Dashboard"))
        self.layout.addWidget(QLabel("Overview of accounts, drafts, and pending tasks."))
        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)
        self.layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        s = self.db.stats()
        cards = [
            ("Accounts", str(s["accounts"])),
            ("Active sessions", str(s["active"])),
            ("Content drafts", str(s["drafts"])),
            ("Pending tasks", str(s["pending_tasks"])),
        ]
        for i, (t, v) in enumerate(cards):
            self.grid.addWidget(stat_card(t, v), 0, i)
