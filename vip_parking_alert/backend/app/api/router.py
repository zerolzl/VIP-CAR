from fastapi import APIRouter

from .spots import router as spots_router
from .contacts import router as contacts_router
from .notify_configs import router as notify_configs_router
from .settings import router as settings_router
from .alerts import router as alerts_router
from .system import router as system_router

api_router = APIRouter()

api_router.include_router(spots_router)
api_router.include_router(contacts_router)
api_router.include_router(notify_configs_router)
api_router.include_router(settings_router)
api_router.include_router(alerts_router)
api_router.include_router(system_router)
