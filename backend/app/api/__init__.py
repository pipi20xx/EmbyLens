from fastapi import APIRouter
from .server import router as server_router
from .stats import router as stats_router
from .system import router as system_router
from .toolkit import router as toolkit_router
from .emby_items import router as emby_items_router
from .tmdb_lookup import router as tmdb_lookup_router
from .tmdb_search import router as tmdb_search_router
from .tmdb_lab import router as tmdb_lab_router
from .bangumi_lab import router as bangumi_lab_router
from .actor_lab import router as actor_lab_router
from .actors import router as actors_router
from .webhook import router as webhook_router
from .dedupe import router as dedupe_router
from .autotags import router as autotags_router
from .docker import router as docker_router
from .docker_compose import router as compose_router
from .pgsql import router as pgsql_router
from .navigation import router as navigation_router
from .auth import router as auth_router
from .backup import router as backup_router
from .notification import router as notification_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(notification_router, prefix="/notification", tags=["Notification"])
router.include_router(backup_router, prefix="/backup", tags=["Backup"])
router.include_router(server_router, prefix="/server", tags=["Server"])
router.include_router(stats_router, prefix="/stats", tags=["Stats"])
router.include_router(system_router, prefix="/system", tags=["System"])
router.include_router(toolkit_router, prefix="/toolkit", tags=["Toolkit"])
router.include_router(emby_items_router, prefix="/items", tags=["EmbyItems"])
router.include_router(tmdb_lookup_router, prefix="/tmdb", tags=["TMDBLookup"])
router.include_router(tmdb_search_router, prefix="/tmdb-search", tags=["TMDBSearch"])
router.include_router(tmdb_lab_router, prefix="/tmdb-lab", tags=["TMDBLab"])
router.include_router(bangumi_lab_router, prefix="/bangumi_lab", tags=["BangumiLab"])
router.include_router(actor_lab_router, prefix="/actor-lab", tags=["ActorLab"])
router.include_router(actors_router, prefix="/actors", tags=["Actors"])
router.include_router(webhook_router, prefix="/webhook", tags=["Webhook"])
router.include_router(dedupe_router, prefix="/dedupe", tags=["Dedupe"])
router.include_router(autotags_router, prefix="/autotags", tags=["AutoTags"])
router.include_router(docker_router, prefix="/docker", tags=["Docker"])
router.include_router(compose_router, prefix="/docker/compose", tags=["DockerCompose"])
router.include_router(pgsql_router, prefix="/pgsql", tags=["PostgreSQL"])
router.include_router(navigation_router, prefix="/navigation", tags=["Navigation"])

@router.get("/status")
async def get_status():
    return {"status": "online"}
