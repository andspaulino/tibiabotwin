from enum import Enum


class FrameStatus(Enum):
    VALID = "valid"
    STALE = "stale"
    FROZEN = "frozen"
    FAILED = "failed"
