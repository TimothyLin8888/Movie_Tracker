from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Movie, User
from routers.auth import get_current_user
from services.import_service import import_imdb

router = APIRouter(
    prefix="/library",
    tags=["Library"]
)

BASE_DIR = Path(__file__).resolve().parent.parent

@router.get("/")
def get_movies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Movie).filter(Movie.user_id == user.id).all()


@router.get("/{movie_id}")
def get_movie(
    movie_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Movie).filter(Movie.id == movie_id, Movie.user_id == user.id).first()


@router.post("/import")
def import_movies(user: User = Depends(get_current_user)):
    csv_path = BASE_DIR / "data" / "IMDbUserRatings.csv"
    result = import_imdb(csv_path, user.id)

    return result


@router.delete("/{movie_id}")
def delete_movie(
    movie_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    movie = db.query(Movie).filter(Movie.id == movie_id, Movie.user_id == user.id).first()

    if movie is None:
        return {
            "message": "Movie not found."
        }

    db.delete(movie)
    db.commit()

    return {
        "message": "Movie deleted successfully."
    }