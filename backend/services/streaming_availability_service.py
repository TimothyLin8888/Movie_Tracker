import os
from datetime import datetime

from sqlalchemy.orm import Session

from database.models import Movie, MovieStreamingAvailability, StreamingService, UserStreamingService
from services import watchmode

# Only subscription access implies "the user has this service" - rent/buy
# availability doesn't tell us anything about a service the user pays for.
SUBSCRIPTION_SOURCE_TYPE = "sub"

# Watchmode's free tier only allows a limited number of requests per month.
# A single run against every movie in the library (1600+ and growing) would
# blow through that in one shot, so each run only processes a capped batch,
# oldest-checked-first, and the rest catch up on later runs.
DEFAULT_DAILY_LIMIT = 50


def get_tracked_services(db: Session) -> list[StreamingService]:
    """Services at least one user has actually selected - no point spending
    Watchmode's quota checking services nobody uses."""
    return (
        db.query(StreamingService)
        .join(UserStreamingService, UserStreamingService.service_id == StreamingService.id)
        .filter(StreamingService.watchmode_name.isnot(None))
        .distinct()
        .all()
    )


def refresh_all_availability(db: Session, limit: int | None = None) -> dict:
    if limit is None:
        limit = int(os.getenv("WATCHMODE_DAILY_LIMIT", DEFAULT_DAILY_LIMIT))

    tracked_services = get_tracked_services(db)
    if not tracked_services:
        return {"movies_checked": 0, "rows_updated": 0, "not_found": 0, "tracked_services": 0, "remaining": 0}

    tracked_service_ids = [service.id for service in tracked_services]
    tracked_by_watchmode_name = {
        service.watchmode_name.strip().lower(): service for service in tracked_services
    }

    identifiable_movies = db.query(Movie).filter(
        (Movie.imdb_id.isnot(None)) | (Movie.tmdb_id.isnot(None))
    )

    # Oldest-checked (or never-checked) movies go first, so a capped batch
    # still rotates through the whole library across successive daily runs.
    movies = (
        identifiable_movies
        .order_by(Movie.watchmode_checked_at.asc().nulls_first())
        .limit(limit)
        .all()
    )
    remaining = max(identifiable_movies.count() - len(movies), 0)

    movies_checked = 0
    rows_updated = 0
    not_found = 0

    for movie in movies:
        if not movie.watchmode_id:
            resolved_id = watchmode.resolve_watchmode_id(movie)
            if not resolved_id:
                not_found += 1
                movie.watchmode_checked_at = datetime.now()
                db.commit()
                continue
            movie.watchmode_id = resolved_id

        sources = watchmode.fetch_sources(movie.watchmode_id)
        movie.watchmode_checked_at = datetime.now()
        movies_checked += 1

        db.query(MovieStreamingAvailability).filter(
            MovieStreamingAvailability.movie_id == movie.id,
            MovieStreamingAvailability.service_id.in_(tracked_service_ids),
        ).delete(synchronize_session=False)

        seen_service_ids = set()
        for source in sources:
            if source.get("type") != SUBSCRIPTION_SOURCE_TYPE:
                continue

            name = (source.get("name") or "").strip().lower()
            service = tracked_by_watchmode_name.get(name)
            if not service or service.id in seen_service_ids:
                continue
            seen_service_ids.add(service.id)

            leaving_date = None
            expires_on = source.get("expires_on")
            if expires_on:
                try:
                    leaving_date = datetime.fromtimestamp(expires_on).date()
                except (TypeError, ValueError, OSError):
                    leaving_date = None

            db.add(MovieStreamingAvailability(
                movie_id=movie.id,
                service_id=service.id,
                leaving_date=leaving_date,
                checked_at=datetime.now(),
            ))
            rows_updated += 1

        db.commit()

    return {
        "movies_checked": movies_checked,
        "rows_updated": rows_updated,
        "not_found": not_found,
        "tracked_services": len(tracked_services),
        "remaining": remaining,
    }
