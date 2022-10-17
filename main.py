from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import redis
import json
from database import SessionLocal, engine, Base
from schema.poems import VerseBase
from models.poems import Verse
from uuid import uuid4
from schema.session import SessionBase, SessionIn, SubmitIn, SessionWithPoemOut

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_redis():
    r = redis.Redis(host="localhost", port=6379, db=0)
    try:
        yield r
    finally:
        r.close()


@app.get("/")
def ping():
    return {"message": "pong"}


SESSION_REDIS_KEY_FORMAT_STRING = "session_id_{}"
SESSION_REDIS_KEY_EXPIRE_TIME = 60 * 60 * 24


@app.get(
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
    r: redis.Redis = Depends(get_session_redis),
):
    verse = db.query(Verse)
    if start:
        verse = verse.filter(Verse.text.startswith(start[0]))
    if session_id:
        redis_key = SESSION_REDIS_KEY_FORMAT_STRING.format(session_id)
        redis_session = r.get(redis_key)
        if not redis_session:
            raise HTTPException(status_code=404, detail="Session not found")
        session = SessionBase(**json.loads(redis_session))
        verse = verse.filter(Verse.text.not_in(session.used_poems))

    verse = verse.order_by(func.random()).first()
    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found")

    return verse


@app.post(
    "/session/join",
    dependencies=[Depends(get_session_redis)],
    response_model=SessionBase,
    tags=["Session"],
    description="Join or create a session",
)
def join_session(
    data: SessionIn,
    r: redis.Redis = Depends(get_session_redis),
):
    redis_key = SESSION_REDIS_KEY_FORMAT_STRING.format(data.session_id)
    redis_session = r.get(redis_key)
    if redis_session:
        redis_session = json.loads(redis_session)
        session = SessionBase(id=redis_session["id"], users=redis_session["users"])
        if data.email not in session.users:
            session.users.append(data.email)
            r.set(redis_key, session.json())
    else:
        session_id = uuid4().hex
        session = SessionBase(id=session_id, users=[data.email])
        r.set(
            SESSION_REDIS_KEY_FORMAT_STRING.format(session_id),
            session.json(),
            ex=SESSION_REDIS_KEY_EXPIRE_TIME,
        )
    return session


@app.post(
    "/session/submit",
    dependencies=[Depends(get_session_redis), Depends(get_db)],
    response_model=SessionWithPoemOut,
    tags=["Session"],
    description="Submit a verse to a session",
)
def submit_verse(
    data: SubmitIn,
    r: redis.Redis = Depends(get_session_redis),
    db: Session = Depends(get_db),
):
    redis_key = SESSION_REDIS_KEY_FORMAT_STRING.format(data.session_id)
    redis_session = r.get(redis_key)
    if not redis_session:
        raise HTTPException(status_code=404, detail="Session not found")
    session = SessionBase(**json.loads(redis_session))
    if data.email not in session.users:
        raise HTTPException(status_code=403, detail="User not in session")
    if session.used_poems and data.verse[0] != session.used_poems[-1][-1]:
        raise HTTPException(status_code=403, detail="Verse does not match")

    verse = db.query(Verse).filter(Verse.text == data.verse.strip()).first()
    if verse is None:
        raise HTTPException(status_code=404, detail="Verse not found")

    if verse.text in session.used_poems:
        session.scores[data.email] = session.scores.get(data.email, 0) - 1
        r.set(
            redis_key,
            session.json(),
            ex=SESSION_REDIS_KEY_EXPIRE_TIME,
        )
        return session

    session.used_poems.append(verse.text)
    session.scores[data.email] = session.scores.get(data.email, 0) + 1
    r.set(
        redis_key,
        session.json(),
        ex=SESSION_REDIS_KEY_EXPIRE_TIME,
    )
    return SessionWithPoemOut(verse=verse, session=session)
