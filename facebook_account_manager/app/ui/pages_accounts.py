from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.accounts.service import AccountService, mask_cookie_preview
from app.browser.manager import BrowserManager
from app.database.db import Database
from app.database.models import Account, AccountStatus
from app.ui.widgets import section_title


class AccountDialog(QDialog):
    def __init__(self, parent=None, account: Account | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Account" if account else "Add Account")
        self.resize(480, 420)
        self.account = account
        form = QFormLayout()
        self.nickname = QLineEdit(account.nickname if account else "")
        self.profile_id = QLineEdit(account.profile_id if account else "")
        self.group = QLineEdit(account.group_name if account else "Default")
        self.tags = QLineEdit(account.tags if account else "")
        self.notes = QTextEdit(account.notes if account else "")
        self.notes.setMaximumHeight(80)
        self.status = QComboBox()
        for s in AccountStatus:
            self.status.addItem(s.value)
        if account:
            idx = self.status.findText(account.status)
            if idx >= 0:
                self.status.setCurrentIndex(idx)
        self.session = QTextEdit()
        self.session.setPlaceholderText(
            "Optional: paste cookie JSON array (user-provided only).\n"
            "Full values are encrypted at rest and never shown in the table."
        )
        self.session.setMaximumHeight(100)
        form.addRow("Nickname *", self.nickname)
        form.addRow("Profile ID", self.profile_id)
        form.addRow("Group", self.group)
        form.addRow("Tags", self.tags)
        form.addRow("Notes", self.notes)
        form.addRow("Status", self.status)
        form.addRow("Session JSON", self.session)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def result_data(self) -> tuple[Account, str | None]:
        acc = Account(
            id=self.account.id if self.account else None,
            nickname=self.nickname.text().strip(),
            profile_id=self.profile_id.text().strip(),
            group_name=self.group.text().strip() or "Default",
            tags=self.tags.text().strip(),
            notes=self.notes.toPlainText().strip(),
            status=self.status.currentText(),
            has_session=bool(self.account and self.account.has_session),
            last_verified=self.account.last_verified if self.account else None,
            last_activity=self.account.last_activity if self.account else None,
        )
        session = self.session.toPlainText().strip() or None
        return acc, session


class AccountsPage(QWidget):
    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self.svc = AccountService(db)
        self.browser = BrowserManager()
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(section_title("Accounts"))

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search nickname, tags, notes…")
        self.search.textChanged.connect(self.refresh)
        self.filter_status = QComboBox()
        self.filter_status.addItem("All statuses", "")
        for s in AccountStatus:
            self.filter_status.addItem(s.value, s.value)
        self.filter_status.currentIndexChanged.connect(self.refresh)
        btn_add = QPushButton("Add")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(self.add_account)
        btn_import = QPushButton("Import")
        btn_import.clicked.connect(self.import_file)
        btn_export = QPushButton("Export metadata")
        btn_export.clicked.connect(self.export_file)
        toolbar.addWidget(self.search, 1)
        toolbar.addWidget(self.filter_status)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_import)
        toolbar.addWidget(btn_export)
        root.addLayout(toolbar)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nickname", "Profile", "Group", "Status", "Session", "Last verified"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table)

        actions = QHBoxLayout()
        for label, slot in [
            ("Edit", self.edit_account),
            ("Clear session", self.clear_session),
            ("Open browser", self.open_browser),
            ("Manual login", self.manual_login),
            ("Delete", self.delete_account),
        ]:
            b = QPushButton(label)
            if label == "Delete":
                b.setObjectName("danger")
            b.clicked.connect(slot)
            actions.addWidget(b)
        actions.addStretch()
        root.addLayout(actions)
        self.refresh()

    def _selected_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self.table.item(rows[0].row(), 0).text())

    def refresh(self) -> None:
        status = self.filter_status.currentData() or None
        search = self.search.text().strip() or None
        accounts = self.db.list_accounts(status=status, search=search)
        self.table.setRowCount(0)
        for a in accounts:
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [
                str(a.id),
                a.nickname,
                a.profile_id,
                a.group_name,
                a.status,
                "Yes" if a.has_session else "No",
                a.last_verified or "—",
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)

    def add_account(self) -> None:
        dlg = AccountDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        acc, session = dlg.result_data()
        try:
            self.svc.create(
                acc.nickname,
                acc.profile_id,
                acc.group_name,
                acc.tags,
                acc.notes,
                session,
            )
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def edit_account(self) -> None:
        aid = self._selected_id()
        if not aid:
            return
        acc = self.db.get_account(aid)
        if not acc:
            return
        dlg = AccountDialog(self, acc)
        if dlg.exec() != QDialog.Accepted:
            return
        data, session = dlg.result_data()
        try:
            self.svc.update(data)
            if session:
                self.svc.set_session(aid, session)
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def clear_session(self) -> None:
        aid = self._selected_id()
        if not aid:
            return
        if QMessageBox.question(self, "Clear session", "Remove encrypted session for this account?") != QMessageBox.Yes:
            return
        self.svc.clear_session(aid)
        self.refresh()

    def delete_account(self) -> None:
        aid = self._selected_id()
        if not aid:
            return
        if QMessageBox.question(self, "Delete", "Permanently delete this account and its session?") != QMessageBox.Yes:
            return
        self.svc.delete(aid)
        self.refresh()

    def open_browser(self) -> None:
        aid = self._selected_id()
        if not aid:
            return
        session = self.db.get_session(aid)
        msg = self.browser.open_for_account(aid, session_json=session)
        QMessageBox.information(self, "Browser", msg)

    def manual_login(self) -> None:
        aid = self._selected_id()
        if not aid:
            return
        msg = self.browser.open_manual_login(aid)
        QMessageBox.information(
            self,
            "Manual login",
            msg + "\n\nLog in yourself in the browser. This app does not capture passwords or auto-steal cookies.",
        )

    def import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import accounts", "", "JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return
        p = Path(path)
        try:
            if p.suffix.lower() == ".csv":
                ok, errors = self.svc.import_csv(p)
            else:
                ok, errors = self.svc.import_json(p)
            msg = f"Imported {ok} account(s)."
            if errors:
                msg += "\n\nIssues:\n" + "\n".join(errors[:20])
            QMessageBox.information(self, "Import", msg)
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Import failed", str(e))

    def export_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export", "accounts_meta.json", "JSON (*.json)")
        if not path:
            return
        n = self.svc.export_json(Path(path))
        QMessageBox.information(self, "Export", f"Exported {n} accounts (sessions excluded).")
