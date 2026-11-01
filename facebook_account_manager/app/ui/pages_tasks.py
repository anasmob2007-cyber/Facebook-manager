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
from app.database.models import ScheduledTask, TaskStatus
from app.scheduler.tasks import HealthChecker, ReminderService
from app.ui.widgets import section_title


class TaskDialog(QDialog):
    def __init__(self, db: Database, task: ScheduledTask | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Task")
        self.task = task
        form = QFormLayout()
        self.account = QComboBox()
        self.account.addItem("(none)", None)
        for a in db.list_accounts():
            self.account.addItem(a.nickname, a.id)
        if task and task.account_id:
            i = self.account.findData(task.account_id)
            if i >= 0:
                self.account.setCurrentIndex(i)
        self.title = QLineEdit(task.title if task else "")
        self.desc = QTextEdit(task.description if task else "")
        self.desc.setMaximumHeight(80)
        self.due = QLineEdit(task.due_at if task and task.due_at else "")
        self.due.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        self.status = QComboBox()
        for s in TaskStatus:
            self.status.addItem(s.value)
        if task:
            i = self.status.findText(task.status)
            if i >= 0:
                self.status.setCurrentIndex(i)
        form.addRow("Account", self.account)
        form.addRow("Title", self.title)
        form.addRow("Description", self.desc)
        form.addRow("Due", self.due)
        form.addRow("Status", self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(buttons)

    def result_task(self) -> ScheduledTask:
        return ScheduledTask(
            id=self.task.id if self.task else None,
            account_id=self.account.currentData(),
            title=self.title.text().strip(),
            description=self.desc.toPlainText().strip(),
            due_at=self.due.text().strip() or None,
            status=self.status.currentText(),
        )


class TasksPage(QWidget):
    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        root = QVBoxLayout(self)
        root.addWidget(section_title("Task scheduler & health"))
        bar = QHBoxLayout()
        add = QPushButton("Add task")
        add.setObjectName("primary")
        add.clicked.connect(self.add)
        done = QPushButton("Mark done")
        done.clicked.connect(self.mark_done)
        delete = QPushButton("Delete")
        delete.setObjectName("danger")
        delete.clicked.connect(self.delete)
        health = QPushButton("Run health check")
        health.clicked.connect(self.health)
        due = QPushButton("Show due reminders")
        due.clicked.connect(self.show_due)
        for b in (add, done, delete, health, due):
            bar.addWidget(b)
        bar.addStretch()
        root.addLayout(bar)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Due", "Status", "Account"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        acc_map = {a.id: a.nickname for a in self.db.list_accounts()}
        self.table.setRowCount(0)
        for t in self.db.list_tasks():
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [
                str(t.id),
                t.title,
                t.due_at or "—",
                t.status,
                acc_map.get(t.account_id, "—"),
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
        dlg = TaskDialog(self.db, parent=self)
        if dlg.exec() == QDialog.Accepted:
            t = dlg.result_task()
            if not t.title:
                QMessageBox.warning(self, "Error", "Title required")
                return
            self.db.add_task(t)
            self.refresh()

    def mark_done(self) -> None:
        tid = self._id()
        if not tid:
            return
        for t in self.db.list_tasks():
            if t.id == tid:
                t.status = TaskStatus.DONE.value
                self.db.update_task(t)
                break
        self.refresh()

    def delete(self) -> None:
        tid = self._id()
        if not tid:
            return
        if QMessageBox.question(self, "Delete", "Delete task?") == QMessageBox.Yes:
            self.db.delete_task(tid)
            self.refresh()

    def health(self) -> None:
        msgs = HealthChecker(self.db).run()
        QMessageBox.information(
            self,
            "Health check",
            "\n".join(msgs) if msgs else "No issues found (local checks only).",
        )
        self.refresh()

    def show_due(self) -> None:
        msgs = ReminderService(self.db).due_tasks()
        QMessageBox.information(
            self,
            "Due reminders",
            "\n".join(msgs) if msgs else "No due tasks.",
        )
