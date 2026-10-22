from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import MovieList, User
from routers.auth import get_current_user
from routers.schedule import upcoming_for_user
from services.stats import compute_stats, watch_cards

router = APIRouter(tags=["Profile"])


class ProfileUpdateRequest(BaseModel):
    bio: str | None = Field(default=None, max_length=280)
    is_public: bool | None = None
    show_lists: bool | None = None


def serialize_settings(user: User):
    return {
        "username": user.username,
        "bio": user.bio,
        "is_public": user.is_public,
        "show_lists": user.show_lists,
    }


@router.get("/profile/me")
def get_profile_settings(user: User = Depends(get_current_user)):
    return serialize_settings(user)


@router.patch("/profile/me")
def update_profile_settings(
    request: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if "bio" in request.model_fields_set:
        user.bio = (request.bio or "").strip() or None
    if request.is_public is not None:
        user.is_public = request.is_public
    if request.show_lists is not None:
        user.show_lists = request.show_lists
    db.commit()
    return serialize_settings(user)


@router.get("/public/{username}")
def get_public_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.username) == username.lower()).first()
    # A private profile and a missing one look identical so usernames can't be probed.
    if user is None or not user.is_active or not user.is_public:
        raise HTTPException(status_code=404, detail="Profile not found")

    lists = None
    if user.show_lists:
        owned = db.query(MovieList).filter(MovieList.user_id == user.id).order_by(MovieList.name).all()
        lists = [{"name": movie_list.name, "count": len(movie_list.memberships)} for movie_list in owned]

    return {
        "username": user.username,
        "bio": user.bio,
        "member_since": user.created_at.date(),
        "stats": compute_stats(db, user.id),
        "schedule": [
            {
                "scheduled_date": item.scheduled_date,
                "title": movie.title,
                "poster_path": movie.poster_path,
                "year": movie.release_date.year if movie.release_date else None,
                "note": item.note,
            }
            for item, movie in upcoming_for_user(db, user.id)
        ],
        "recent": watch_cards(db, user.id, limit=12),
        "favorites": watch_cards(db, user.id, limit=12, favorites_only=True),
        "lists": lists,
    }
