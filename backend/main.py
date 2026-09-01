from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, search, library

from database.database import Base, engine
from database.models import Movie, User

app = FastAPI()


origins =[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
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