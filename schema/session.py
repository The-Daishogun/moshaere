from pydantic import BaseModel
from .poems import VerseBase


class SessionBase(BaseModel):
    id: str
    users: list[str]
    used_poems: list[str] = []
    scores: dict[str, int] = {}


class SessionIn(BaseModel):
    email: str
    session_id: str | None = None


class SubmitIn(SessionIn):
    verse: str
    session_id: str


class SessionWithPoemOut(BaseModel):
    verse: VerseBase
    session: SessionBase
