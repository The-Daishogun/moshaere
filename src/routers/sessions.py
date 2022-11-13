from fastapi import APIRouter, Depends, HTTPException
from src.deps.db import get_db
from src.deps.redis import get_session_redis
from sqlalchemy.orm import Session
from redis import Redis
from src.models.poems import Verse
from uuid import uuid4
from src.schema.session import (
    NewSession,
    SessionBase,
    SessionIn,
    SubmitIn,
    SessionWithPoemOut,
)
from src.rulesets.validations import Validations

from src.schema.session import SessionBase

router = APIRouter()


@router.post(
    "/session/new",
    response_model=SessionBase,
    tags=["Session"],
    description="Create a new session",
)
def new_session(
    data: NewSession,
    r: Redis = Depends(get_session_redis),
):
    session_id = uuid4().hex
    session = SessionBase(
        id=session_id, users=[data.email], validation_slug=data.validation_slug
    )
    session.set(r)
    return session


@router.post(
    "/session/join",
    dependencies=[Depends(get_session_redis)],
    response_model=SessionBase,
    tags=["Session"],
    description="Join or create a session",
)
def join_session(
    data: SessionIn,
    r: Redis = Depends(get_session_redis),
):
    session = SessionBase.get_session_by_session_id(data.session_id, r)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if data.email in session.users:
        raise HTTPException(status_code=400, detail="User already in session")

    session.users.append(data.email)
    session.set(r)
    return session


@router.post(
    "/session/submit",
    dependencies=[Depends(get_session_redis), Depends(get_db)],
    response_model=SessionWithPoemOut,
    tags=["Session"],
    description="Submit a verse to a session",
)
def submit_verse(
    data: SubmitIn,
    r: Redis = Depends(get_session_redis),
    db: Session = Depends(get_db),
):
    session = SessionBase.get_session_by_session_id(data.session_id, r)
    if not session:
        raise HTTPException(status_code=404, detail={"error": "Session not found"})
    if data.email not in session.users:
        raise HTTPException(status_code=403, detail={"error": "User not in session"})
    current_turn = session.get_current_turn()
    if current_turn != data.email:
        raise HTTPException(
            status_code=400, detail={"error": "not your turn", "turn": current_turn}
        )

    validation_class = Validations.get_validation_class(session.validation_slug)
    valid, reason, verse = validation_class.validate(data.verse, session, db)

    if not valid or reason or verse is None:
        session.change_score(data.email, -1)
        session.set(r)
        return SessionWithPoemOut(verse=None, session=session, error=reason)

    session.used_poems.append(verse.text if isinstance(verse, Verse) else verse)  # type: ignore
    session.turn += 1
    session.change_score(data.email, 1)
    session.set(r)
    return SessionWithPoemOut(verse=verse, session=session)
