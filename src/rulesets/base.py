from abc import ABC, abstractclassmethod
from sqlalchemy.orm import Session
from ..models.poems import Verse
from src.schema.session import SessionBase


class BaseValidation(ABC):
    slug: str

    @abstractclassmethod
    def validate(
        self, verse: str, session: SessionBase, db: Session
    ) -> tuple[bool, str, Verse | str | None]:
        raise NotImplementedError
