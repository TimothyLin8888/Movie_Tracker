from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database.database import get_db
from database.models import ListMembership, Movie, MovieList, User, WatchHistory
from routers.auth import get_current_user
from services.stats import compute_stats

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/summary")
def get_summary(
    list_id: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if list_id is not None:
        owned = db.query(MovieList).filter(MovieList.id == list_id, MovieList.user_id == user.id).first()
        if owned is None:
            raise HTTPException(status_code=404, detail="List not found")
    return compute_stats(db, user.id, list_id)


@router.get("/")
def get_analytics(
    list_id: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    selected_list = None
    if list_id is not None:
        selected_list = db.query(MovieList).filter(MovieList.id == list_id, MovieList.user_id == user.id).first()
        if selected_list is None:
            raise HTTPException(status_code=404, detail="List not found")

    watches = (
        db.query(WatchHistory, Movie)
        .join(Movie, Movie.id == WatchHistory.movie_id)
        .filter(WatchHistory.user_id == user.id)
    )
    if selected_list:
        watches = watches.join(ListMembership, ListMembership.watch_id == WatchHistory.id)
        watches = watches.filter(ListMembership.list_id == selected_list.id)
    watches = (
        watches
        .order_by(WatchHistory.watch_date.asc())
        .all()
    )

    return [
        {
            "id": movie.id,
            "title": movie.title,
            "watch_date": watch.watch_date,
            "personal_rating": watch.personal_rating,
            "runtime": movie.runtime,
            "genres": movie.genres,
            "favorite": bool(watch.is_favorite),
            "list_ids": [membership.list_id for membership in watch.list_memberships],
        }
        for watch, movie in watches
    ]
