from fastapi import APIRouter
from .server import router as server_router
from .stats import router as stats_router
from .system import router as system_router
from .toolkit import router as toolkit_router
from .emby_items import router as emby_items_router
from .tmdb_lookup import router as tmdb_lookup_router
from .tmdb_search import router as tmdb_search_router
from .actors import router as actors_router
from .webhook import router as webhook_router
from .dedupe import router as dedupe_router

router = APIRouter()

router.include_router(server_router, prefix="/server", tags=["Server"])
router.include_router(stats_router, prefix="/stats", tags=["Stats"])
router.include_router(system_router, prefix="/system", tags=["System"])
router.include_router(toolkit_router, prefix="/toolkit", tags=["Toolkit"])
router.include_router(emby_items_router, prefix="/items", tags=["EmbyItems"])
router.include_router(tmdb_lookup_router, prefix="/tmdb", tags=["TMDBLookup"])
router.include_router(tmdb_search_router, prefix="/tmdb-search", tags=["TMDBSearch"])
router.include_router(actors_router, prefix="/actors", tags=["Actors"])
router.include_router(webhook_router, prefix="/webhook", tags=["Webhook"])
router.include_router(dedupe_router, prefix="/dedupe", tags=["Deduplication"])

@router.get("/status")
async def get_status():
    return {"status": "online"}