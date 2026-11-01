"""Reusable UI pieces."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


def stat_card(title: str, value: str) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(
        "QFrame { background-color: #25262b; border: 1px solid #373a40; border-radius: 10px; padding: 12px; }"
    )
    lay = QVBoxLayout(frame)
    t = QLabel(title)
    t.setObjectName("muted")
    v = QLabel(value)
    v.setObjectName("stat")
    lay.addWidget(t)
    lay.addWidget(v)
    return frame


def section_title(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setObjectName("title")
    return lab


def hbox(*widgets: QWidget, stretch_last: bool = False) -> QHBoxLayout:
    lay = QHBoxLayout()
    for i, w in enumerate(widgets):
        lay.addWidget(w)
        if stretch_last and i == len(widgets) - 1:
            lay.setStretch(i, 1)
    return lay
