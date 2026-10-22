from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Movie, MovieStreamingAvailability, StreamingService, User, UserStreamingService
from routers.auth import get_current_user
from services.streaming_availability_service import refresh_all_availability

router = APIRouter(prefix="/streaming-services", tags=["Streaming services"])

DEFAULT_SERVICES = (
    # (slug, display name, logo key, Watchmode's source name for this service)
    ("netflix", "Netflix", "netflix", "Netflix"),
    ("disney-plus", "Disney+", "disney-plus", "Disney Plus"),
    ("max", "Max", "max", "Max"),
    ("prime-video", "Prime Video", "prime-video", "Amazon Prime Video"),
    ("apple-tv", "Apple TV+", "apple-tv", "Apple TV+"),
    ("hulu", "Hulu", "hulu", "Hulu"),
    ("paramount-plus", "Paramount+", "paramount-plus", "Paramount Plus"),
    ("peacock", "Peacock", "peacock", "Peacock"),
)


class StreamingServiceSelection(BaseModel):
    service_slugs: list[str] = Field(default_factory=list)


def ensure_default_services(db: Session):
    existing_by_slug = {
        service.slug: service for service in db.query(StreamingService).all()
    }
    changed = False
    for slug, name, logo_key, watchmode_name in DEFAULT_SERVICES:
        existing = existing_by_slug.get(slug)
        if existing is None:
            db.add(StreamingService(
                slug=slug, name=name, logo_key=logo_key, watchmode_name=watchmode_name,
            ))
            changed = True
        elif existing.watchmode_name != watchmode_name:
            # Backfill watchmode_name for services created before this column existed.
            existing.watchmode_name = watchmode_name
            changed = True
    if changed:
        db.commit()


def serialize_service(service: StreamingService):
    return {
        "id": service.id,
        "slug": service.slug,
        "name": service.name,
        "logo_key": service.logo_key,
    }


@router.get("")
def list_streaming_services(db: Session = Depends(get_db)):
    ensure_default_services(db)
    services = (
        db.query(StreamingService)
        .filter(StreamingService.is_active.is_(True))
        .order_by(StreamingService.name)
        .all()
    )
    return [serialize_service(service) for service in services]


@router.get("/me")
def get_my_streaming_services(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_default_services(db)
    selected_services = (
        db.query(StreamingService)
        .join(UserStreamingService, UserStreamingService.service_id == StreamingService.id)
        .filter(
            UserStreamingService.user_id == user.id,
            StreamingService.is_active.is_(True),
        )
        .order_by(StreamingService.name)
        .all()
    )
    return [serialize_service(service) for service in selected_services]


@router.put("/me")
def replace_my_streaming_services(
    request: StreamingServiceSelection,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_default_services(db)
    requested_slugs = set(request.service_slugs)
    services = (
        db.query(StreamingService)
        .filter(
            StreamingService.slug.in_(requested_slugs),
            StreamingService.is_active.is_(True),
        )
        .all()
        if requested_slugs
        else []
    )
    found_slugs = {service.slug for service in services}
    unknown_slugs = requested_slugs - found_slugs
    if unknown_slugs:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown streaming service(s): {', '.join(sorted(unknown_slugs))}",
        )

    db.query(UserStreamingService).filter(
        UserStreamingService.user_id == user.id
    ).delete(synchronize_session=False)
    db.add_all([
        UserStreamingService(user_id=user.id, service_id=service.id)
        for service in services
    ])
    db.commit()

    return {
        "services": [serialize_service(service) for service in sorted(services, key=lambda item: item.name)],
    }


@router.post("/refresh-availability")
def refresh_availability(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger a Watchmode refresh instead of waiting for the daily job - useful while testing."""
    return refresh_all_availability(db)


@router.get("/leaving-soon")
def get_leaving_soon(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(MovieStreamingAvailability, Movie, StreamingService)
        .join(Movie, Movie.id == MovieStreamingAvailability.movie_id)
        .join(StreamingService, StreamingService.id == MovieStreamingAvailability.service_id)
        .join(
            UserStreamingService,
            (UserStreamingService.service_id == StreamingService.id)
            & (UserStreamingService.user_id == user.id),
        )
        .filter(MovieStreamingAvailability.leaving_date.isnot(None))
        .order_by(MovieStreamingAvailability.leaving_date)
        .all()
    )

    return [
        {
            "movie_id": movie.id,
            "title": movie.title,
            "poster_path": movie.poster_path,
            "service": serialize_service(service),
            "leaving_date": availability.leaving_date,
        }
        for availability, movie, service in rows
    ]
