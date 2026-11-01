"""Dark theme stylesheet."""
from app.core.config import (
    ACCENT,
    ACCENT_HOVER,
    DANGER,
    DARK_BG,
    DARK_BORDER,
    DARK_SURFACE,
    SUCCESS,
    TEXT,
    TEXT_MUTED,
    WARNING,
)

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT};
    font-family: 'Segoe UI', 'Inter', 'SF Pro Text', sans-serif;
    font-size: 13px;
}}
QFrame#sidebar {{
    background-color: {DARK_SURFACE};
    border-right: 1px solid {DARK_BORDER};
}}
QPushButton {{
    background-color: {DARK_SURFACE};
    border: 1px solid {DARK_BORDER};
    border-radius: 6px;
    padding: 8px 14px;
    color: {TEXT};
}}
QPushButton:hover {{
    background-color: {DARK_BORDER};
}}
QPushButton#primary {{
    background-color: {ACCENT};
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton#danger {{
    background-color: {DANGER};
    border: none;
    color: white;
}}
QPushButton#nav {{
    text-align: left;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    background: transparent;
}}
QPushButton#nav:checked, QPushButton#nav:hover {{
    background-color: {ACCENT};
    color: white;
}}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDateTimeEdit {{
    background-color: {DARK_BG};
    border: 1px solid {DARK_BORDER};
    border-radius: 6px;
    padding: 8px;
    color: {TEXT};
    selection-background-color: {ACCENT};
}}
QTableWidget, QTableView, QListWidget, QTreeWidget {{
    background-color: {DARK_SURFACE};
    border: 1px solid {DARK_BORDER};
    border-radius: 8px;
    gridline-color: {DARK_BORDER};
    alternate-background-color: {DARK_BG};
}}
QHeaderView::section {{
    background-color: {DARK_SURFACE};
    color: {TEXT_MUTED};
    border: none;
    border-bottom: 1px solid {DARK_BORDER};
    padding: 8px;
    font-weight: 600;
}}
QLabel#title {{
    font-size: 20px;
    font-weight: 700;
}}
QLabel#muted {{
    color: {TEXT_MUTED};
}}
QLabel#stat {{
    font-size: 28px;
    font-weight: 700;
    color: {ACCENT};
}}
QGroupBox {{
    border: 1px solid {DARK_BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}
QStatusBar {{
    background: {DARK_SURFACE};
    border-top: 1px solid {DARK_BORDER};
}}
QScrollBar:vertical {{
    background: {DARK_BG};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {DARK_BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QTabWidget::pane {{
    border: 1px solid {DARK_BORDER};
    border-radius: 8px;
}}
QTabBar::tab {{
    background: {DARK_SURFACE};
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {ACCENT};
    color: white;
}}
"""
