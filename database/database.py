from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine("postgresql://moshaere:moshaere@localhost:5432/moshaere")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
