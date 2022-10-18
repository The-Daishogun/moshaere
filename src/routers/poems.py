from fastapi import APIRouter, Depends, HTTPException
from src.schema.poems import VerseBase
from src.deps.db import get_db
from src.deps.redis import get_session_redis
from sqlalchemy.orm import Session
from redis import Redis
from src.models.poems import Verse
from sqlalchemy import func

from src.schema.session import SessionBase

router = APIRouter()


@router.get(
    "/verse/random",
    response_model=VerseBase,
    dependencies=[Depends(get_db)],
    description="Get a random verse from a random poem",
    tags=["Verses"],
)
def get_random_verse(
    start: str | None = None,
    session_id: str | None = None,
    db: Session = Depends(get_db),
    r: Redis = Depends(get_session_redis),
):
    verse = db.query(Verse)
    if start:
        verse = verse.filter(Verse.text.startswith(start[0]))
    if session_id:
        session = SessionBase.get_session_by_session_id(session_id, r)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        verse = verse.filter(Verse.text.not_in(session.used_poems))

    verse = verse.order_by(func.random()).first()
    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found")

    return verse
