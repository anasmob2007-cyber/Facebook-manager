from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.config import APP_NAME, APP_VERSION
from app.database.db import Database
from app.ui.pages_accounts import AccountsPage
from app.ui.pages_content import ContentPage
from app.ui.pages_dashboard import DashboardPage
from app.ui.pages_logs import LogsPage
from app.ui.pages_settings import SettingsPage
from app.ui.pages_tasks import TasksPage
from app.ui.styles import STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1100, 720)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(STYLESHEET)

        self.db = Database()
        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Sidebar
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(220)
        side_lay = QVBoxLayout(side)
        brand = QLabel(APP_NAME)
        brand.setObjectName("title")
        brand.setWordWrap(True)
        side_lay.addWidget(brand)
        side_lay.addWidget(QLabel(f"v{APP_VERSION}"))
        side_lay.addSpacing(12)

        self.stack = QStackedWidget()
        self.pages = {
            "Dashboard": DashboardPage(self.db),
            "Accounts": AccountsPage(self.db),
            "Content": ContentPage(self.db),
            "Tasks": TasksPage(self.db),
            "Logs": LogsPage(self.db),
            "Settings": SettingsPage(self.db),
        }
        self.nav_buttons: list[QPushButton] = []
        for name, page in self.pages.items():
            self.stack.addWidget(page)
            btn = QPushButton(name)
            btn.setObjectName("nav")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, n=name: self._navigate(n))
            side_lay.addWidget(btn)
            self.nav_buttons.append(btn)
        side_lay.addStretch()
        note = QLabel("Authorized accounts only.\nNo password storage.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        side_lay.addWidget(note)

        outer.addWidget(side)
        outer.addWidget(self.stack, 1)
        self._navigate("Dashboard")
        self.statusBar().showMessage("Ready")

    def _navigate(self, name: str) -> None:
        page = self.pages[name]
        self.stack.setCurrentWidget(page)
        for btn in self.nav_buttons:
            btn.setChecked(btn.text() == name)
        if hasattr(page, "refresh"):
            page.refresh()
        self.statusBar().showMessage(name)
