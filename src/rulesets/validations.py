from enum import Enum
from sqlalchemy.orm import Session
from .base import BaseValidation
from ..models.poems import Verse
from typing import Type
from dataclasses import dataclass


class NoValidation(BaseValidation):
    from ..schema.session import SessionBase

    slug = "no_validation"

    @classmethod
    def validate(
        cls, verse: str, session: SessionBase, db: Session
    ) -> tuple[bool, str, str]:
        return True, "", verse


class WithBasicValidation(BaseValidation):
    from ..schema.session import SessionBase

    slug = "with_basic_validation"

    @classmethod
    def validate(
        cls, verse: str, session: SessionBase, db: Session
    ) -> tuple[bool, str, str]:
        reason = session.run_basic_verse_validation(verse)
        return not bool(reason), reason, verse


class WithPoemValidation(BaseValidation):
    from ..schema.session import SessionBase

    slug = "with_poem_validation"

    @classmethod
    def validate(
        cls, verse: str, session: SessionBase, db: Session
    ) -> tuple[bool, str, Verse | None]:
        reason = session.run_basic_verse_validation(verse)

        if reason:
            return False, reason, None

        verse_obj: Verse | None = db.query(Verse).filter(Verse.text == verse).first()
        if not verse_obj:
            return False, "Verse not found", verse_obj

        return True, "", verse_obj


class Validations(str, Enum):
    NO_VALIDATION = NoValidation.slug
    BASIC_VALIDATION = WithBasicValidation.slug
    POEM_VALIDATION = WithPoemValidation.slug

    @staticmethod
    def get_validation_class(slug: str) -> Type[BaseValidation]:
        SLUG_2_CLASS = {
            NoValidation.slug: NoValidation,
            WithBasicValidation.slug: WithBasicValidation,
            WithPoemValidation.slug: WithPoemValidation,
        }
        return SLUG_2_CLASS[slug]
