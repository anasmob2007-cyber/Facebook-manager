from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.database.db import Database
from app.ui.widgets import section_title


class LogsPage(QWidget):
    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        root = QVBoxLayout(self)
        root.addWidget(section_title("Activity logs"))
        bar = QHBoxLayout()
        ref = QPushButton("Refresh")
        ref.clicked.connect(self.refresh)
        bar.addWidget(ref)
        bar.addStretch()
        root.addLayout(bar)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Time", "Account", "Action", "Detail"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        acc_map = {a.id: a.nickname for a in self.db.list_accounts()}
        self.table.setRowCount(0)
        for log in self.db.list_activity():
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [
                log.created_at or "",
                acc_map.get(log.account_id, "—"),
                log.action,
                log.detail,
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
