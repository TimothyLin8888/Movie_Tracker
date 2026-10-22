import zipfile
from datetime import date as date_type

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import ListMembership, Movie, MovieList, User, WatchHistory
from routers.auth import get_current_user
from services.import_service import backfill_movie_details, import_imdb, import_letterboxd
from services.movies import get_or_create_movie

router = APIRouter(
    prefix="/library",
    tags=["Library"]
)


class ListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class AddMovieRequest(BaseModel):
    tmdb_id: int
    title: str
    poster: str | None = None
    date: date_type | None = None
    description: str | None = None
    rating: int = Field(ge=0, le=10)
    watch_date: date_type | None = None
    list_ids: list[int] = []


class WatchUpdateRequest(BaseModel):
    rating: int | None = Field(default=None, ge=0, le=10)
    watch_date: date_type | None = None
    is_favorite: bool | None = None


def serialize_watch(watch: WatchHistory, movie: Movie):
    return {
        "watch_id": watch.id,
        "movie_id": movie.id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "poster_path": movie.poster_path,
        "release_date": movie.release_date,
        "runtime": movie.runtime,
        "genres": movie.genres,
        "director": movie.director,
        "rating": watch.personal_rating,
        "watch_date": watch.watch_date,
        "is_favorite": watch.is_favorite,
    }


@router.get("/lists")
def get_lists(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lists = db.query(MovieList).filter(MovieList.user_id == user.id).order_by(MovieList.name).all()
    return [{"id": movie_list.id, "name": movie_list.name, "count": len(movie_list.memberships)} for movie_list in lists]


@router.post("/lists", status_code=201)
def create_list(request: ListRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="List name cannot be empty")
    existing = db.query(MovieList).filter(MovieList.user_id == user.id, MovieList.name.ilike(name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already have a list with that name")
    movie_list = MovieList(user_id=user.id, name=name)
    db.add(movie_list)
    db.commit()
    db.refresh(movie_list)
    return {"id": movie_list.id, "name": movie_list.name, "count": 0}


@router.post("/add")
def add_movie(request: AddMovieRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    owned_lists = db.query(MovieList).filter(MovieList.user_id == user.id, MovieList.id.in_(request.list_ids)).all() if request.list_ids else []
    if len(owned_lists) != len(set(request.list_ids)):
        raise HTTPException(status_code=403, detail="One or more selected lists are not yours")

    movie = get_or_create_movie(
        db,
        tmdb_id=request.tmdb_id,
        title=request.title,
        poster=request.poster,
        release_date=request.date,
        overview=request.description,
    )

    watch = db.query(WatchHistory).filter(WatchHistory.user_id == user.id, WatchHistory.movie_id == movie.id).first()
    if watch:
        watch.personal_rating = request.rating
        if request.watch_date:
            watch.watch_date = request.watch_date
    else:
        watch = WatchHistory(
            user_id=user.id,
            movie_id=movie.id,
            watch_date=request.watch_date or date_type.today(),
            personal_rating=request.rating,
        )
        db.add(watch)
        db.flush()

    current_list_ids = {membership.list_id for membership in watch.list_memberships}
    for movie_list in owned_lists:
        if movie_list.id not in current_list_ids:
            db.add(ListMembership(list_id=movie_list.id, watch_id=watch.id))

    db.commit()
    return {"id": movie.id, "watch_id": watch.id, "title": movie.title, "rating": watch.personal_rating}


@router.get("/")
def get_watches(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(WatchHistory, Movie)
        .join(Movie, Movie.id == WatchHistory.movie_id)
        .filter(WatchHistory.user_id == user.id)
        .order_by(WatchHistory.watch_date.desc(), WatchHistory.id.desc())
        .all()
    )
    return [serialize_watch(watch, movie) for watch, movie in rows]


def get_own_watch(db: Session, user: User, watch_id: int) -> WatchHistory:
    watch = db.query(WatchHistory).filter(WatchHistory.id == watch_id, WatchHistory.user_id == user.id).first()
    if watch is None:
        raise HTTPException(status_code=404, detail="Watch not found")
    return watch


@router.patch("/watches/{watch_id}")
def update_watch(
    watch_id: int,
    request: WatchUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watch = get_own_watch(db, user, watch_id)
    if request.rating is not None:
        watch.personal_rating = request.rating
    if request.watch_date is not None:
        watch.watch_date = request.watch_date
    if request.is_favorite is not None:
        watch.is_favorite = request.is_favorite
    db.commit()
    return serialize_watch(watch, watch.movie)


@router.delete("/watches/{watch_id}")
def delete_watch(
    watch_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only this user's watch is removed; the shared Movie row stays for everyone else.
    watch = get_own_watch(db, user, watch_id)
    db.delete(watch)
    db.commit()
    return {"message": "Watch deleted"}


@router.post("/backfill")
def backfill(limit: int = 100, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return backfill_movie_details(db, user.id, limit=min(max(limit, 1), 500))


# Imports run in chunks: the client re-sends the file with a growing offset until next_offset is null,
# so no single request has to wait on hundreds of TMDB lookups.
@router.post("/import/imdb")
def import_imdb_csv(
    file: UploadFile,
    offset: int = 0,
    limit: int = 40,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return import_imdb(file.file, user.id, db, offset=max(offset, 0), limit=min(max(limit, 1), 100))
    except (KeyError, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        raise HTTPException(status_code=400, detail=f"That doesn't look like an IMDb ratings export: {error}")


@router.post("/import/letterboxd")
def import_letterboxd_csv(
    file: UploadFile,
    offset: int = 0,
    limit: int = 40,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return import_letterboxd(file.file, user.id, db, offset=max(offset, 0), limit=min(max(limit, 1), 100))
    except (KeyError, ValueError, zipfile.BadZipFile, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        raise HTTPException(status_code=400, detail=f"That doesn't look like a Letterboxd export: {error}")
