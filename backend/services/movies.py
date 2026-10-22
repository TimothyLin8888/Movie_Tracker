from datetime import date, datetime

from sqlalchemy.orm import Session

from database.models import Movie
from services.tmdb import fetch_movie_details


def parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def apply_details(movie: Movie, details: dict) -> None:
    """Fill in missing Movie fields from TMDB details without overwriting what is already stored."""
    for field in ("imdb_id", "poster_path", "overview", "runtime", "genres", "director", "original_language"):
        if getattr(movie, field) in (None, "") and details.get(field):
            setattr(movie, field, details[field])
    if movie.release_date is None:
        movie.release_date = parse_date(details.get("release_date"))


def get_or_create_movie(
    db: Session,
    tmdb_id: int,
    title: str | None = None,
    poster: str | None = None,
    release_date=None,
    overview: str | None = None,
    session=None,
) -> Movie:
    """Movies are shared by all users and keyed by tmdb_id; new ones are enriched from TMDB straight away."""
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    if movie:
        return movie

    movie = Movie(
        tmdb_id=tmdb_id,
        title=title,
        poster_path=poster,
        release_date=parse_date(release_date),
        overview=overview,
        media_type="movie",
    )
    details = fetch_movie_details(tmdb_id, session=session)
    if details:
        movie.title = movie.title or details["title"]
        apply_details(movie, details)
    db.add(movie)
    db.flush()
    return movie
