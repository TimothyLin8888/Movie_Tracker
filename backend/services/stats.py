from collections import Counter
from datetime import date

from sqlalchemy.orm import Session

from database.models import ListMembership, Movie, WatchHistory


def _user_watches(db: Session, user_id: int, list_id: int | None = None):
    query = (
        db.query(WatchHistory, Movie)
        .join(Movie, Movie.id == WatchHistory.movie_id)
        .filter(WatchHistory.user_id == user_id)
    )
    if list_id is not None:
        query = query.join(ListMembership, ListMembership.watch_id == WatchHistory.id).filter(
            ListMembership.list_id == list_id
        )
    return query


def _top(counter: Counter, limit: int, key: str = "name"):
    return [{key: name, "count": count} for name, count in counter.most_common(limit)]


def _last_12_months(today: date) -> list[str]:
    months = []
    year, month = today.year, today.month
    for _ in range(12):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(months))


def compute_stats(db: Session, user_id: int, list_id: int | None = None) -> dict:
    rows = _user_watches(db, user_id, list_id).all()

    ratings = [watch.personal_rating for watch, _ in rows if watch.personal_rating is not None]
    runtimes = [movie.runtime for _, movie in rows if movie.runtime and movie.runtime > 0]

    per_year = Counter(watch.watch_date.year for watch, _ in rows if watch.watch_date)
    per_month = Counter(watch.watch_date.strftime("%Y-%m") for watch, _ in rows if watch.watch_date)
    rating_counts = Counter(ratings)
    genres = Counter(
        genre.strip()
        for _, movie in rows
        for genre in (movie.genres or "").split(",")
        if genre.strip()
    )
    directors = Counter(movie.director for _, movie in rows if movie.director)
    languages = Counter(movie.original_language for _, movie in rows if movie.original_language)
    decades = Counter(
        f"{movie.release_date.year // 10 * 10}s" for _, movie in rows if movie.release_date
    )

    top_rated = sorted(
        (row for row in rows if row[0].personal_rating is not None),
        key=lambda row: (row[0].personal_rating, row[0].watch_date or date.min),
        reverse=True,
    )[:5]

    return {
        "totals": {
            "films": len(rows),
            "hours": round(sum(runtimes) / 60, 1),
            "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
            "avg_runtime": round(sum(runtimes) / len(runtimes)) if runtimes else None,
            "favorites": sum(1 for watch, _ in rows if watch.is_favorite),
        },
        "films_per_year": [{"year": year, "count": per_year[year]} for year in sorted(per_year)],
        "films_per_month": [
            {"month": month, "count": per_month.get(month, 0)} for month in _last_12_months(date.today())
        ],
        "rating_distribution": [{"rating": value, "count": rating_counts.get(value, 0)} for value in range(0, 11)],
        "top_genres": _top(genres, 8),
        "top_directors": _top(directors, 5),
        "languages": _top(languages, 5, key="code"),
        "decades": [{"decade": decade, "count": decades[decade]} for decade in sorted(decades)],
        "top_rated": [
            {
                "title": movie.title,
                "poster_path": movie.poster_path,
                "rating": watch.personal_rating,
                "watch_date": watch.watch_date,
            }
            for watch, movie in top_rated
        ],
    }


def watch_cards(db: Session, user_id: int, limit: int = 12, favorites_only: bool = False) -> list[dict]:
    query = _user_watches(db, user_id)
    if favorites_only:
        query = query.filter(WatchHistory.is_favorite.is_(True))
    rows = query.order_by(WatchHistory.watch_date.desc(), WatchHistory.id.desc()).limit(limit).all()
    return [
        {
            "title": movie.title,
            "poster_path": movie.poster_path,
            "rating": watch.personal_rating,
            "watch_date": watch.watch_date,
            "year": movie.release_date.year if movie.release_date else None,
        }
        for watch, movie in rows
    ]
