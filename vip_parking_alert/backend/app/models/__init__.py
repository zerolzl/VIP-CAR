from .base import Base
from .spot import VipParkingSpot
from .contact import Contact
from .notify_config import SpotNotifyConfig
from .alert_log import AlertLog
from .external_db import ExternalDbConfig
from .sms_gateway import SmsGatewayConfig

__all__ = [
    "Base",
    "VipParkingSpot",
    "Contact",
    "SpotNotifyConfig",
    "AlertLog",
    "ExternalDbConfig",
    "SmsGatewayConfig",
]
