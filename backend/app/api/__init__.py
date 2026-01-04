from fastapi import APIRouter
from .server import router as server_router
from .stats import router as stats_router
from .system import router as system_router
from .toolkit import router as toolkit_router
from .emby_items import router as emby_items_router

router = APIRouter()

router.include_router(server_router, prefix="/server", tags=["Server"])
router.include_router(stats_router, prefix="/stats", tags=["Stats"])
router.include_router(system_router, prefix="/system", tags=["System"])
router.include_router(toolkit_router, prefix="/toolkit", tags=["Toolkit"])
router.include_router(emby_items_router, prefix="/items", tags=["EmbyItems"])

@router.get("/status")
async def get_status():
    return {"status": "online"}