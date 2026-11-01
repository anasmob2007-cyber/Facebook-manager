"""SQLite schema helpers and row types."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class AccountStatus(str, Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"
    REQUIRES_LOGIN = "Requires Login"
    ERROR = "Error"
    UNKNOWN = "Unknown"


class PublishStatus(str, Enum):
    DRAFT = "Draft"
    SCHEDULED = "Scheduled"
    PUBLISHED = "Published"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class TaskStatus(str, Enum):
    PENDING = "Pending"
    DONE = "Done"
    CANCELLED = "Cancelled"


@dataclass
class Account:
    id: Optional[int] = None
    nickname: str = ""
    profile_id: str = ""
    group_name: str = "Default"
    tags: str = ""  # comma-separated
    notes: str = ""
    status: str = AccountStatus.UNKNOWN.value
    last_verified: Optional[str] = None
    last_activity: Optional[str] = None
    has_session: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ContentDraft:
    id: Optional[int] = None
    account_id: Optional[int] = None
    title: str = ""
    body: str = ""
    media_note: str = ""
    status: str = PublishStatus.DRAFT.value
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ScheduledTask:
    id: Optional[int] = None
    account_id: Optional[int] = None
    title: str = ""
    description: str = ""
    due_at: Optional[str] = None
    status: str = TaskStatus.PENDING.value
    created_at: Optional[str] = None


@dataclass
class ActivityLog:
    id: Optional[int] = None
    account_id: Optional[int] = None
    action: str = ""
    detail: str = ""
    created_at: Optional[str] = None
