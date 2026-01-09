from enum import Enum


class IssueStatus(str, Enum):
    open = "OPEN"
    in_progress = "IN_PROGRESS"
    resolved = "RESOLVED"
    closed = "CLOSED"
