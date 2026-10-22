import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import analytics, auth, search, library, streaming, schedule, profile

from database.database import Base, engine
from database import models  # noqa: F401  (registers all tables with Base)

app = FastAPI()

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(search.router)
app.include_router(auth.router)
app.include_router(library.router)
app.include_router(analytics.router)
app.include_router(streaming.router)
app.include_router(schedule.router)
app.include_router(profile.router)
