from fastapi import FastAPI
from src.database import engine, Base
from src.routers import poems, sessions

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def ping():
    return {"message": "pong"}


app.include_router(poems.router)
app.include_router(sessions.router)
