from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.media import MediaItem

router = APIRouter()

@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    # 电影总数
    movies_count = await db.scalar(
        select(func.count(MediaItem.id)).where(MediaItem.item_type == "Movie")
    )
    # 剧集总数
    series_count = await db.scalar(
        select(func.count(MediaItem.id)).where(MediaItem.item_type == "Series")
    )
    
    # 查找重复项数 (具有相同 tmdb_id 且数量 > 1 的组)
    # 统计有多少个 tmdb_id 是重复的
    query = (
        select(MediaItem.tmdb_id)
        .where(MediaItem.tmdb_id != None)
        .where(MediaItem.tmdb_id != "")
        .group_by(MediaItem.tmdb_id)
        .having(func.count(MediaItem.id) > 1)
    )
    
    result = await db.execute(query)
    duplicates_groups = len(result.all())

    return {
        "movies": movies_count or 0,
        "series": series_count or 0,
        "duplicates": duplicates_groups,
        "status": "connected" if (movies_count or series_count) else "idle"
    }