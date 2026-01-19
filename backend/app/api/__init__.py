from fastapi import APIRouter
from .server import router as server_router
from .stats import router as stats_router
from .system import router as system_router
from .toolkit import router as toolkit_router
from .emby_items import router as emby_items_router
from .tmdb_lookup import router as tmdb_lookup_router
from .tmdb_search import router as tmdb_search_router
from .tmdb_lab import router as tmdb_lab_router
from .actor_lab import router as actor_lab_router
from .actors import router as actors_router
from .webhook import router as webhook_router
from .dedupe import router as dedupe_router
from .autotags import router as autotags_router
from .docker import router as docker_router
from .docker_compose import router as compose_router

router = APIRouter()
...
router.include_router(docker_router, prefix="/docker", tags=["Docker"])
router.include_router(compose_router, prefix="/docker/compose", tags=["DockerCompose"])

@router.get("/status")
async def get_status():
    return {"status": "online"}