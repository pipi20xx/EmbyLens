from fastapi import APIRouter
from .server import router as server_router
from .stats import router as stats_router
from .system import router as system_router
from .toolkit import router as toolkit_router

router = APIRouter()

router.include_router(server_router, prefix="/server", tags=["Server"])
router.include_router(stats_router, prefix="/stats", tags=["Stats"])
router.include_router(system_router, prefix="/system", tags=["System"])
router.include_router(toolkit_router, prefix="/toolkit", tags=["Toolkit"])

@router.get("/status")
async def get_status():
    return {"status": "online"}