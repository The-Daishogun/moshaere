from typing_extensions import Self
from pydantic import BaseModel
from redis import Redis

from .poems import VerseBase
import json


class SessionBase(BaseModel):
    id: str
    validation_slug: str
    users: list[str]
    used_poems: list[str] = []
    scores: dict[str, int] = {}

    SESSION_REDIS_KEY_FORMAT_STRING = "session_id_{}"
    SESSION_REDIS_KEY_EXPIRE_TIME = 60 * 60 * 24

    @classmethod
    def get_session_by_session_id(cls, session_id: str, r: Redis) -> Self | None:
        redis_key = cls.SESSION_REDIS_KEY_FORMAT_STRING.format(session_id)
        redis_session = r.get(redis_key)
        if not redis_session:
            return None
        return SessionBase(**json.loads(redis_session))

    @property
    def session_key(self):
        return self.SESSION_REDIS_KEY_FORMAT_STRING.format(self.id)

    def set(self, r: Redis):
        return r.set(
            self.session_key,
            self.json(),
            ex=self.SESSION_REDIS_KEY_EXPIRE_TIME,
        )

    def run_basic_verse_validation(self, verse: str) -> str:
        if self.used_poems and verse[0] != self.used_poems[-1][-1]:
            return "Verse does not match"
        return ""

    def change_score(self, email: str, score: int) -> int:
        self.scores[email] = self.scores.get(email, 0) + score
        return self.scores[email]


class NewSession(BaseModel):
    from src.rulesets.validations import Validations

    email: str
    validation_slug: Validations


class SessionIn(BaseModel):
    email: str
    session_id: str


class SubmitIn(SessionIn):
    verse: str
    session_id: str


class SessionWithPoemOut(BaseModel):
    verse: VerseBase | None
    session: SessionBase
    error: str | None = None
