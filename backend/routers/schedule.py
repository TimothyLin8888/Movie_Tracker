from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Movie, ScheduledWatch, User, WatchHistory
from routers.auth import get_current_user
from services.movies import get_or_create_movie

router = APIRouter(prefix="/schedule", tags=["Schedule"])


class ScheduleRequest(BaseModel):
    tmdb_id: int
    title: str
    poster: str | None = None
    date: date_type | None = None
    description: str | None = None
    scheduled_date: date_type
    note: str | None = Field(default=None, max_length=200)


class ScheduleUpdateRequest(BaseModel):
    scheduled_date: date_type | None = None
    note: str | None = Field(default=None, max_length=200)


class MarkWatchedRequest(BaseModel):
    rating: int = Field(ge=0, le=10)
    watch_date: date_type | None = None


def serialize_item(item: ScheduledWatch, movie: Movie):
    return {
        "id": item.id,
        "movie_id": movie.id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "poster_path": movie.poster_path,
        "year": movie.release_date.year if movie.release_date else None,
        "scheduled_date": item.scheduled_date,
        "note": item.note,
    }


def get_own_item(db: Session, user: User, item_id: int) -> ScheduledWatch:
    item = db.query(ScheduledWatch).filter(ScheduledWatch.id == item_id, ScheduledWatch.user_id == user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Scheduled movie not found")
    return item


def upcoming_for_user(db: Session, user_id: int, include_past: bool = False):
    query = (
        db.query(ScheduledWatch, Movie)
        .join(Movie, Movie.id == ScheduledWatch.movie_id)
        .filter(ScheduledWatch.user_id == user_id)
    )
    if not include_past:
        query = query.filter(ScheduledWatch.scheduled_date >= date_type.today())
    return query.order_by(ScheduledWatch.scheduled_date, ScheduledWatch.id).all()


@router.get("")
def list_schedule(
    include_past: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [serialize_item(item, movie) for item, movie in upcoming_for_user(db, user.id, include_past)]


@router.post("", status_code=201)
def schedule_movie(
    request: ScheduleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if request.scheduled_date < date_type.today():
        raise HTTPException(status_code=400, detail="Pick today or a future date")

    movie = get_or_create_movie(
        db,
        tmdb_id=request.tmdb_id,
        title=request.title,
        poster=request.poster,
        release_date=request.date,
        overview=request.description,
    )
    note = (request.note or "").strip() or None
    item = ScheduledWatch(user_id=user.id, movie_id=movie.id, scheduled_date=request.scheduled_date, note=note)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="That movie is already scheduled for that day")
    return serialize_item(item, movie)


@router.patch("/{item_id}")
def update_scheduled(
    item_id: int,
    request: ScheduleUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_own_item(db, user, item_id)
    if request.scheduled_date is not None:
        if request.scheduled_date < date_type.today():
            raise HTTPException(status_code=400, detail="Pick today or a future date")
        item.scheduled_date = request.scheduled_date
    if "note" in request.model_fields_set:
        item.note = (request.note or "").strip() or None
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="That movie is already scheduled for that day")
    return serialize_item(item, item.movie)


@router.delete("/{item_id}")
def delete_scheduled(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_own_item(db, user, item_id)
    db.delete(item)
    db.commit()
    return {"message": "Removed from your schedule"}


@router.post("/{item_id}/watched")
def mark_watched(
    item_id: int,
    request: MarkWatchedRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_own_item(db, user, item_id)
    title = item.movie.title
    watch_date = request.watch_date or date_type.today()

    watch = db.query(WatchHistory).filter(WatchHistory.user_id == user.id, WatchHistory.movie_id == item.movie_id).first()
    if watch:
        watch.personal_rating = request.rating
        watch.watch_date = watch_date
    else:
        watch = WatchHistory(
            user_id=user.id, movie_id=item.movie_id, watch_date=watch_date, personal_rating=request.rating
        )
        db.add(watch)

    db.delete(item)
    db.commit()
    return {"watch_id": watch.id, "title": title, "rating": watch.personal_rating}
