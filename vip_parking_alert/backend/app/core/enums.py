import enum


class NotifyType(str, enum.Enum):
    SMS = "sms"
    WEBHOOK = "webhook"


class SpotStatus(int, enum.Enum):
    DISABLED = 0
    ENABLED = 1
