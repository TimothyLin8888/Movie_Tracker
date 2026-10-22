import csv
import io
import os
import zipfile
from datetime import date, datetime
from pathlib import PurePosixPath

import pandas as pd
import requests
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import ListMembership, Movie, MovieList, WatchHistory
from services.movies import apply_details, get_or_create_movie
from services.tmdb import fetch_movie_details

MAX_NOT_FOUND_TITLES = 50

# Folders inside a Letterboxd export that hold archived/removed entries, not current data.
IGNORED_FOLDERS = {"deleted", "orphaned"}
KNOWN_FOLDERS = IGNORED_FOLDERS | {"likes", "lists"}


def _tmdb_get(session: requests.Session, path: str, params: dict):
    try:
        response = session.get(
            f"https://api.themoviedb.org/3{path}",
            params={"api_key": os.getenv("TMDB_API_KEY"), **params},
            timeout=10,
        )
    except requests.exceptions.RequestException:
        return None
    return response.json() if response.status_code == 200 else None


def _add_watch(db: Session, user_id: int, movie: Movie, watch_date, rating) -> tuple[WatchHistory, bool]:
    """Returns (watch, created). When the user already has the movie their existing rating is kept."""
    existing = (
        db.query(WatchHistory)
        .filter(WatchHistory.user_id == user_id, WatchHistory.movie_id == movie.id)
        .first()
    )
    if existing:
        return existing, False
    watch = WatchHistory(user_id=user_id, movie_id=movie.id, watch_date=watch_date, personal_rating=rating)
    db.add(watch)
    db.flush()
    return watch, True


def _parse_iso_date(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def _require_columns(rows: pd.DataFrame, *columns: str) -> None:
    missing = [column for column in columns if column not in rows.columns]
    if missing:
        raise ValueError(f"missing column(s): {', '.join(missing)}")


def _first_column(rows: pd.DataFrame, *names: str) -> str:
    for name in names:
        if name in rows.columns:
            return name
    raise ValueError(f"missing column: one of {', '.join(names)}")


def _decode(raw: bytes) -> str:
    """Files saved by hand are sometimes cp1252 instead of UTF-8; accept both (and a leading BOM)."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def _read_csv_text(text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(text))


def _read_upload(file) -> bytes:
    file.seek(0)
    return file.read()


def _new_result(total: int, offset: int, limit: int, **counters) -> dict:
    end = offset + limit
    return {
        "total": total,
        "next_offset": end if end < total else None,
        "not_found_titles": [],
        **counters,
    }


def import_imdb(csv_file, user_id: int, db: Session, offset: int = 0, limit: int = 40) -> dict:
    rows = _read_csv_text(_decode(_read_upload(csv_file)))
    # IMDb has used two export layouts over the years; accept both.
    id_column = _first_column(rows, "Title ID", "Const")
    rating_column = _first_column(rows, "Rating", "Your Rating")
    date_column = _first_column(rows, "Last Modified Date", "Date Rated")
    title_column = "Title" if "Title" in rows.columns else None

    session = requests.Session()
    result = _new_result(
        len(rows), offset, limit, imported_movies=0, skipped_tv=0, not_found=0, duplicates=0, database_errors=0
    )

    def not_found(row, imdb_id):
        result["not_found"] += 1
        if len(result["not_found_titles"]) < MAX_NOT_FOUND_TITLES:
            result["not_found_titles"].append(str(row[title_column]) if title_column else str(imdb_id))

    for _, row in rows.iloc[offset : offset + limit].iterrows():
        try:
            imdb_id = row[id_column]
            rating = int(row[rating_column])
            watch_date = _parse_iso_date(row[date_column])

            movie = db.query(Movie).filter(Movie.imdb_id == imdb_id).first()
            if movie is None:
                found = _tmdb_get(session, f"/find/{imdb_id}", {"external_source": "imdb_id"})
                if found is None:
                    not_found(row, imdb_id)
                    continue
                if found.get("tv_results") and not found.get("movie_results"):
                    result["skipped_tv"] += 1
                    continue
                if not found.get("movie_results"):
                    not_found(row, imdb_id)
                    continue
                tmdb_movie = found["movie_results"][0]
                movie = get_or_create_movie(
                    db,
                    tmdb_id=tmdb_movie["id"],
                    title=tmdb_movie.get("title"),
                    poster=tmdb_movie.get("poster_path"),
                    release_date=tmdb_movie.get("release_date"),
                    session=session,
                )
                if not movie.imdb_id:
                    movie.imdb_id = imdb_id

            _, created = _add_watch(db, user_id, movie, watch_date, rating)
            result["imported_movies" if created else "duplicates"] += 1
            db.commit()
        except Exception:
            db.rollback()
            result["database_errors"] += 1

    return result


def _zip_entries(archive: zipfile.ZipFile) -> dict[str, str]:
    """Map 'watched.csv' / 'likes/films.csv' / 'lists/x.csv' -> the real entry name in the zip.

    Letterboxd also ships deleted/ and orphaned/ copies of diary.csv etc. Those are ignored (matching by file
    name alone let them overwrite the real diary). A single wrapper folder, from re-zipping the extracted
    export, is tolerated.
    """
    named = [(info.filename, PurePosixPath(info.filename.lower().replace("\\", "/")).parts) for info in archive.infolist() if not info.is_dir()]
    first_parts = {parts[0] for _, parts in named if len(parts) > 1}
    strip_wrapper = bool(named) and all(len(parts) > 1 for _, parts in named) and len(first_parts) == 1 and not (first_parts & KNOWN_FOLDERS)

    entries: dict[str, str] = {}
    for real_name, parts in named:
        relative = parts[1:] if strip_wrapper else parts
        if not relative or relative[0] in IGNORED_FOLDERS:
            continue
        entries["/".join(relative)] = real_name
    return entries


def _film_key(name, year) -> tuple[str, int]:
    return str(name).strip(), int(year)


def _parse_letterboxd_list(text: str) -> tuple[str, list[tuple[int, str, int]]]:
    """A list export is a one-row metadata block, a blank line, then Position,Name,Year,URL,Description rows."""
    rows = list(csv.reader(io.StringIO(text)))
    meta_header = next(i for i, row in enumerate(rows) if row and row[0] == "Date")
    list_name = rows[meta_header + 1][1].strip()
    table_header = next(i for i, row in enumerate(rows) if row and row[0] == "Position")
    columns = rows[table_header]
    entries = []
    for row in rows[table_header + 1 :]:
        if len(row) < len(columns) or not row[0].strip():
            continue
        record = dict(zip(columns, row))
        if not record.get("Year", "").strip():
            continue
        entries.append((int(record["Position"]), record["Name"].strip(), int(record["Year"])))
    return list_name, entries


def _letterboxd_films(file) -> tuple[pd.DataFrame, dict]:
    """Normalise a Letterboxd upload into one row per film: Name, Year, Rating, Date, Favorite, Lists.

    Accepts one CSV (ratings.csv, diary.csv or watched.csv) or the whole export zip. From a zip, watched.csv gives
    the film list, ratings.csv the ratings, diary.csv the real watch dates (the Date column in the other files is
    only when the film was logged), likes/films.csv and profile.csv the favorites, and lists/*.csv the lists.
    """
    raw = _read_upload(file)
    info = {"unwatched_in_lists": 0}

    if not zipfile.is_zipfile(io.BytesIO(raw)):
        frame = _read_csv_text(_decode(raw))
        _require_columns(frame, "Name", "Year")
        if "Watched Date" in frame.columns and "Date" in frame.columns:
            dates = frame["Watched Date"].fillna(frame["Date"])
        else:
            dates = frame[_first_column(frame, "Watched Date", "Date")]
        ratings = frame["Rating"] if "Rating" in frame.columns else float("nan")
        films = pd.DataFrame({"Name": frame["Name"], "Year": frame["Year"], "Rating": ratings, "Date": dates})
        films = films.dropna(subset=["Name", "Year", "Date"])
        films["Year"] = films["Year"].astype(int)
        # A diary lists every viewing; keep one row per film with its latest date (and that viewing's rating).
        films = films.sort_values("Date", kind="stable").groupby(["Name", "Year"], sort=False).last().reset_index()
        films["Favorite"] = False
        films["Lists"] = [[] for _ in range(len(films))]
        return films, info

    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = _zip_entries(archive)
        read = lambda key: _read_csv_text(_decode(archive.read(entries[key]))) if key in entries else None  # noqa: E731
        sources = {key: read(key) for key in ("watched.csv", "ratings.csv", "diary.csv")}
        if all(frame is None for frame in sources.values()):
            raise ValueError("the zip has no watched.csv, ratings.csv or diary.csv")

        films: dict[tuple[str, int], dict] = {}
        for source in ("watched.csv", "ratings.csv", "diary.csv"):
            frame = sources[source]
            if frame is None:
                continue
            _require_columns(frame, "Name", "Year")
            for _, row in frame.dropna(subset=["Name", "Year"]).iterrows():
                entry = films.setdefault(
                    _film_key(row["Name"], row["Year"]),
                    {"rating": None, "date": None, "diary": None, "uri": None, "favorite": False, "lists": []},
                )
                if "Rating" in frame.columns and not pd.isna(row["Rating"]) and entry["rating"] is None:
                    entry["rating"] = float(row["Rating"])
                if source == "diary.csv":
                    watched = row.get("Watched Date")
                    if not pd.isna(watched) and (entry["diary"] is None or str(watched) > entry["diary"]):
                        entry["diary"] = str(watched)
                else:
                    if entry["date"] is None and not pd.isna(row.get("Date")):
                        entry["date"] = str(row["Date"])
                    if entry["uri"] is None and not pd.isna(row.get("Letterboxd URI")):
                        entry["uri"] = str(row["Letterboxd URI"]).strip()

        liked = read("likes/films.csv")
        if liked is not None and {"Name", "Year"} <= set(liked.columns):
            for _, row in liked.dropna(subset=["Name", "Year"]).iterrows():
                entry = films.get(_film_key(row["Name"], row["Year"]))
                if entry:
                    entry["favorite"] = True

        profile = read("profile.csv")
        if profile is not None and "Favorite Films" in profile.columns and len(profile):
            pinned = {link.strip() for link in str(profile["Favorite Films"].iloc[0]).split(",") if link.strip()}
            for entry in films.values():
                if entry["uri"] in pinned:
                    entry["favorite"] = True

        for key in sorted(k for k in entries if k.startswith("lists/") and k.endswith(".csv")):
            try:
                list_name, members = _parse_letterboxd_list(_decode(archive.read(entries[key])))
            except (StopIteration, IndexError, KeyError, ValueError):
                continue  # a list file we can't read shouldn't stop the film import
            for position, name, year in members:
                entry = films.get((name, year))
                if entry and list_name:
                    entry["lists"].append((list_name, position))
                else:
                    info["unwatched_in_lists"] += 1

    today = date.today().isoformat()
    frame = pd.DataFrame(
        [
            {
                "Name": name,
                "Year": year,
                "Rating": data["rating"],
                "Date": data["diary"] or data["date"] or today,
                "Favorite": data["favorite"],
                "Lists": data["lists"],
            }
            for (name, year), data in films.items()
        ],
        columns=["Name", "Year", "Rating", "Date", "Favorite", "Lists"],
    )
    return frame, info


def _apply_extras(db: Session, user_id: int, watch: WatchHistory, favorite: bool, lists: list, cache: dict, result: dict) -> None:
    if favorite and not watch.is_favorite:
        watch.is_favorite = True
        result["favorites_set"] += 1

    for list_name, position in lists:
        key = list_name.lower()
        movie_list = cache.get(key)
        if movie_list is None:
            movie_list = (
                db.query(MovieList)
                .filter(MovieList.user_id == user_id, func.lower(MovieList.name) == key)
                .first()
            )
            if movie_list is None:
                movie_list = MovieList(user_id=user_id, name=list_name[:80])
                db.add(movie_list)
                db.flush()
                result["lists_created"] += 1
            cache[key] = movie_list

        membership = (
            db.query(ListMembership)
            .filter(ListMembership.list_id == movie_list.id, ListMembership.watch_id == watch.id)
            .first()
        )
        if membership is None:
            db.add(ListMembership(list_id=movie_list.id, watch_id=watch.id, position=position))
            result["list_entries_added"] += 1
        elif membership.position is None:
            membership.position = position


def import_letterboxd(file, user_id: int, db: Session, offset: int = 0, limit: int = 40) -> dict:
    films, info = _letterboxd_films(file)
    session = requests.Session()
    result = _new_result(
        len(films),
        offset,
        limit,
        imported_movies=0,
        not_found=0,
        duplicates=0,
        database_errors=0,
        favorites_set=0,
        list_entries_added=0,
        lists_created=0,
    )
    if offset == 0:
        result["lists_skipped_unwatched"] = info["unwatched_in_lists"]
    list_cache: dict[str, MovieList] = {}

    for _, row in films.iloc[offset : offset + limit].iterrows():
        title = str(row["Name"])
        try:
            year = int(row["Year"])
            watch_date = datetime.strptime(str(row["Date"]), "%Y-%m-%d").date()
            # Letterboxd rates 0.5 to 5 in half steps; this app stores 0 to 10.
            rating = None if pd.isna(row["Rating"]) else round(float(row["Rating"]) * 2)

            found = _tmdb_get(session, "/search/movie", {"query": title, "year": year})
            if not found or not found.get("results"):
                result["not_found"] += 1
                if len(result["not_found_titles"]) < MAX_NOT_FOUND_TITLES:
                    result["not_found_titles"].append(f"{title} ({year})")
                continue
            tmdb_movie = found["results"][0]
            movie = get_or_create_movie(
                db,
                tmdb_id=tmdb_movie["id"],
                title=tmdb_movie.get("title"),
                poster=tmdb_movie.get("poster_path"),
                release_date=tmdb_movie.get("release_date"),
                session=session,
            )

            watch, created = _add_watch(db, user_id, movie, watch_date, rating)
            result["imported_movies" if created else "duplicates"] += 1
            # Applied even to films already in the library, so re-running the import fills in favorites/lists.
            _apply_extras(db, user_id, watch, bool(row["Favorite"]), row["Lists"], list_cache, result)
            db.commit()
        except Exception:
            db.rollback()
            list_cache.clear()
            result["database_errors"] += 1

    return result


def backfill_movie_details(db: Session, user_id: int, limit: int = 100) -> dict:
    """Fill runtime/genres/director for this user's movies that were stored without them."""
    session = requests.Session()
    base = (
        db.query(Movie)
        .join(WatchHistory, WatchHistory.movie_id == Movie.id)
        .filter(WatchHistory.user_id == user_id, Movie.runtime.is_(None), Movie.tmdb_id.isnot(None))
    )
    movies = base.limit(limit).all()
    updated = failed = 0

    for movie in movies:
        details = fetch_movie_details(movie.tmdb_id, session=session)
        if not details:
            failed += 1
            continue
        apply_details(movie, details)
        if movie.runtime is None:
            # TMDB has no runtime for it; store 0 so it isn't retried forever (stats ignore 0)
            movie.runtime = 0
        db.commit()
        updated += 1

    remaining = base.count()
    return {"updated": updated, "failed": failed, "remaining": remaining}
