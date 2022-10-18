from pydantic import BaseModel


class PoetBase(BaseModel):
    class Config:
        orm_mode = True

    id: int
    name: str
    description: str


class PoemBase(BaseModel):
    class Config:
        orm_mode = True

    id: int
    poet: PoetBase
    title: str
    url: str


class VerseBase(BaseModel):
    class Config:
        orm_mode = True

    poem: PoemBase
    order: int
    text: str
