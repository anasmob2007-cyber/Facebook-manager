from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.db import Database
from app.database.models import ContentDraft, PublishStatus
from app.ui.widgets import section_title


class DraftDialog(QDialog):
    def __init__(self, db: Database, draft: ContentDraft | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit draft" if draft else "New draft")
        self.resize(520, 400)
        self.draft = draft
        self.db = db
        form = QFormLayout()
        self.account = QComboBox()
        self.account.addItem("(none)", None)
        for a in db.list_accounts():
            self.account.addItem(f"{a.nickname} (#{a.id})", a.id)
        if draft and draft.account_id:
            idx = self.account.findData(draft.account_id)
            if idx >= 0:
                self.account.setCurrentIndex(idx)
        self.title = QLineEdit(draft.title if draft else "")
        self.body = QTextEdit(draft.body if draft else "")
        self.media = QLineEdit(draft.media_note if draft else "")
        self.status = QComboBox()
        for s in PublishStatus:
            self.status.addItem(s.value)
        if draft:
            i = self.status.findText(draft.status)
            if i >= 0:
                self.status.setCurrentIndex(i)
        self.scheduled = QLineEdit(draft.scheduled_at if draft and draft.scheduled_at else "")
        self.scheduled.setPlaceholderText("YYYY-MM-DD HH:MM:SS (reminder only)")
        form.addRow("Account", self.account)
        form.addRow("Title", self.title)
        form.addRow("Body", self.body)
        form.addRow("Media note", self.media)
        form.addRow("Status", self.status)
        form.addRow("Schedule reminder", self.scheduled)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(buttons)

    def result_draft(self) -> ContentDraft:
        return ContentDraft(
            id=self.draft.id if self.draft else None,
            account_id=self.account.currentData(),
            title=self.title.text().strip(),
            body=self.body.toPlainText(),
            media_note=self.media.text().strip(),
            status=self.status.currentText(),
            scheduled_at=self.scheduled.text().strip() or None,
            published_at=self.draft.published_at if self.draft else None,
        )


class ContentPage(QWidget):
    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        root = QVBoxLayout(self)
        root.addWidget(section_title("Content calendar & drafts"))
        bar = QHBoxLayout()
        add = QPushButton("New draft")
        add.setObjectName("primary")
        add.clicked.connect(self.add)
        edit = QPushButton("Edit")
        edit.clicked.connect(self.edit)
        delete = QPushButton("Delete")
        delete.setObjectName("danger")
        delete.clicked.connect(self.delete)
        bar.addWidget(add)
        bar.addWidget(edit)
        bar.addWidget(delete)
        bar.addStretch()
        root.addLayout(bar)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Account", "Title", "Status", "Scheduled", "Updated"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        drafts = self.db.list_drafts()
        acc_map = {a.id: a.nickname for a in self.db.list_accounts()}
        self.table.setRowCount(0)
        for d in drafts:
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [
                str(d.id),
                acc_map.get(d.account_id, "—"),
                d.title,
                d.status,
                d.scheduled_at or "—",
                d.updated_at or "—",
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)

    def _id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self.table.item(rows[0].row(), 0).text())

    def add(self) -> None:
        dlg = DraftDialog(self.db, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.db.add_draft(dlg.result_draft())
            self.refresh()

    def edit(self) -> None:
        did = self._id()
        if not did:
            return
        drafts = {d.id: d for d in self.db.list_drafts()}
        d = drafts.get(did)
        if not d:
            return
        dlg = DraftDialog(self.db, d, self)
        if dlg.exec() == QDialog.Accepted:
            self.db.update_draft(dlg.result_draft())
            self.refresh()

    def delete(self) -> None:
        did = self._id()
        if not did:
            return
        if QMessageBox.question(self, "Delete", "Delete this draft?") == QMessageBox.Yes:
            self.db.delete_draft(did)
            self.refresh()
