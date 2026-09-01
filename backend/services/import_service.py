import pandas as pd
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

from database.database import SessionLocal
from database.models import Movie, WatchHistory

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")


def import_imdb(csv_file, user_id):

    db = SessionLocal()

    movies = pd.read_csv(csv_file)

    imported = 0
    skipped_tv = 0
    not_found = 0
    database_errors = 0
    duplicates = 0

    for _, row in movies.iterrows():

        imdb_id = row["Title ID"]
        rating = int(row["Rating"])

        watch_date = datetime.fromisoformat(
            row["Last Modified Date"].replace("Z", "+00:00")
        ).date()

        movie = (
            db.query(Movie)
            .filter(Movie.imdb_id == imdb_id)
            .first()
        )

        if not movie:

            url = f"https://api.themoviedb.org/3/find/{imdb_id}"

            response = requests.get(
                url,
                params={
                    "api_key": TMDB_API_KEY,
                    "external_source": "imdb_id"
                }
            )

            if response.status_code != 200:
                print(
                    f"TMDB error for {imdb_id}: "
                    f"{response.status_code}"
                )
                continue

            data = response.json()

            movie_results = data.get("movie_results", [])
            tv_results = data.get("tv_results", [])

            if tv_results:
                skipped_tv += 1
                continue

            if not movie_results:
                print(
                    f"TMDB could not find: {imdb_id}"
                )
                not_found += 1
                continue

            tmdb_movie = movie_results[0]

            release_date = None

            if tmdb_movie.get("release_date"):
                release_date = datetime.strptime(
                    tmdb_movie["release_date"],
                    "%Y-%m-%d"
                ).date()

            movie = Movie(
                imdb_id=imdb_id,
                tmdb_id=tmdb_movie.get("id"),
                title=tmdb_movie.get("title"),
                poster_path=tmdb_movie.get("poster_path"),
                release_date=release_date,
                media_type="movie"
            )

            try:
                db.add(movie)
                db.flush()

                print(
                    f"Added movie: {movie.title} "
                    f"(TMDB: {movie.tmdb_id})"
                )

            except Exception as e:
                db.rollback()

                database_errors += 1

                print(
                    f"Database error for {imdb_id}:"
                )
                print(e)

                continue

        existing_watch = (
            db.query(WatchHistory)
            .filter(
                WatchHistory.user_id == user_id,
                WatchHistory.movie_id == movie.id
            )
            .first()
        )

        if existing_watch:
            print(
                f"Skipping duplicate: "
                f"{movie.title}"
            )

            duplicates += 1
            continue

        watch = WatchHistory(
            user_id=user_id,
            movie_id=movie.id,
            watch_date=watch_date,
            personal_rating=rating
        )

        try:
            db.add(watch)
            db.flush()

            imported += 1

            print(
                f"Added watch: {movie.title} "
                f"(Rating: {rating})"
            )

        except Exception as e:
            db.rollback()

            database_errors += 1

            print(
                f"Database error for {imdb_id}:"
            )
            print(e)

    db.commit()
    db.close()

    print()
    print("IMDb import complete.")
    print(f"Imported watches: {imported}")
    print(f"Skipped TV shows: {skipped_tv}")
    print(f"Not found on TMDB: {not_found}")
    print(f"Duplicates skipped: {duplicates}")
    print(f"Database errors: {database_errors}")

    return {
        "imported_movies": imported,
        "skipped_tv": skipped_tv,
        "not_found": not_found,
        "duplicates": duplicates,
        "database_errors": database_errors
    }

def import_letterboxd(csv_file, user_id):

    db = SessionLocal()

    movies = pd.read_csv(csv_file)

    imported = 0
    not_found = 0
    database_errors = 0
    duplicates = 0

    for _, row in movies.iterrows():

        movie_title = row["Name"]
        movie_year = int(row["Year"])
        rating = int(row["Rating"])

        watch_date = datetime.strptime(
            row["Date"],
            "%Y-%m-%d"
        ).date()

        url = "https://api.themoviedb.org/3/search/movie"

        response = requests.get(
            url,
            params={
                "api_key": TMDB_API_KEY,
                "query": movie_title,
                "year": movie_year
            }
        )

        if response.status_code != 200:
            print(
                f"TMDB error for {movie_title}: "
                f"{response.status_code}"
            )
            not_found += 1
            continue

        data = response.json()

        movie_results = data.get("results", [])

        if not movie_results:
            print(
                f"TMDB could not find: "
                f"{movie_title} ({movie_year})"
            )
            not_found += 1
            continue

        tmdb_movie = movie_results[0]

        tmdb_id = tmdb_movie.get("id")

        # Check if movie already exists
        movie = (
            db.query(Movie)
            .filter(Movie.tmdb_id == tmdb_id)
            .first()
        )

        # Create movie if it doesn't exist
        if not movie:

            release_date = None

            if tmdb_movie.get("release_date"):
                release_date = datetime.strptime(
                    tmdb_movie["release_date"],
                    "%Y-%m-%d"
                ).date()

            movie = Movie(
                tmdb_id=tmdb_id,
                title=tmdb_movie.get("title"),
                poster_path=tmdb_movie.get("poster_path"),
                release_date=release_date,
                media_type="movie"
            )

            try:
                db.add(movie)
                db.flush()

            except Exception as e:
                db.rollback()

                database_errors += 1

                print(
                    f"Database error for {movie_title}:"
                )
                print(e)

                continue

        # Check if this user already watched it
        existing_watch = (
            db.query(WatchHistory)
            .filter(
                WatchHistory.user_id == user_id,
                WatchHistory.movie_id == movie.id
            )
            .first()
        )

        if existing_watch:

            print(
                f"Skipping duplicate: "
                f"{movie_title}"
            )

            duplicates += 1
            continue

        # Create watch history
        watch = WatchHistory(
            user_id=user_id,
            movie_id=movie.id,
            watch_date=watch_date,
            personal_rating=rating
        )

        try:

            db.add(watch)
            db.flush()

            imported += 1

            print(
                f"Added: {movie_title}"
            )

        except Exception as e:

            db.rollback()

            database_errors += 1

            print(
                f"Database error for {movie_title}"
            )
            print(e)

    db.commit()
    db.close()

    print()
    print("Letterboxd import complete.")
    print(f"Imported movies: {imported}")
    print(f"Not found on TMDB: {not_found}")
    print(f"Database errors: {database_errors}")
    print(f"Duplicates skipped: {duplicates}")

    return {
        "imported_movies": imported,
        "duplicates": duplicates,
        "not_found": not_found,
        "database_errors": database_errors
    }