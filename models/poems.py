from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship


class Poet(Base):
    __tablename__ = "poets"

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    description = Column(Text)
    poems = relationship("Poem", back_populates="poet")


class Poem(Base):
    __tablename__ = "poems"

    id = Column(Integer, primary_key=True)
    poet_id = Column(Integer, ForeignKey("poets.id"))
    poet = relationship(Poet, back_populates="poems")
    title = Column(Text)
    url = Column(Text)
    verses = relationship("Verse", back_populates="poem")


class Verse(Base):
    __tablename__ = "verses"

    id = Column(Integer, primary_key=True)
    poem_id = Column(Integer, ForeignKey("poems.id"))
    poem = relationship(Poem, back_populates="verses")
    order = Column(Integer)
    text = Column(Text)
