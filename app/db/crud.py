

async def get_all_missions(db):
    from sqlalchemy import select
    from app.db.models import MissionDB
    result = await db.execute(select(MissionDB).order_by(MissionDB.created_at.desc()))
    return list(result.scalars().all())
