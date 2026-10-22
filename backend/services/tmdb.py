import httpx
import os

import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")


def fetch_movie_details(tmdb_id: int, session: requests.Session | None = None) -> dict | None:
    """One TMDB call (with credits) returning the fields analytics needs; None on any failure."""
    getter = session.get if session else requests.get
    try:
        response = getter(
            f"https://api.themoviedb.org/3/movie/{tmdb_id}",
            params={"api_key": os.getenv("TMDB_API_KEY"), "append_to_response": "credits"},
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return None

    data = response.json()
    director = next(
        (person["name"] for person in data.get("credits", {}).get("crew", []) if person.get("job") == "Director"),
        None,
    )
    genres = ", ".join(genre["name"] for genre in data.get("genres", [])) or None
    return {
        "imdb_id": data.get("imdb_id") or None,
        "title": data.get("title"),
        "poster_path": data.get("poster_path"),
        "release_date": data.get("release_date") or None,
        "overview": data.get("overview") or None,
        "runtime": data.get("runtime") or None,
        "genres": genres,
        "director": director,
        "original_language": data.get("original_language"),
        "imdb_rating": None,
    }

async def lookup_imdb_id(imdb_id: str):
    # TMDB has a find endpoint that takes IMDb IDs directly
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "external_source": "imdb_id"
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params)
        data = res.json()

    # TMDB returns separate lists for movies vs TV
    if data.get("movie_results"):
        movie = data["movie_results"][0]
        return {
            "tmdb_id": movie["id"],
            "imdb_id": imdb_id,
            "title": movie["title"],
            "media_type": "movie",
            "release_date": movie.get("release_date"),
            "poster_path": movie.get("poster_path"),
        }
    elif data.get("tv_results"):
        show = data["tv_results"][0]
        return {
            "tmdb_id": show["id"],
            "imdb_id": imdb_id,
            "title": show["name"],
            "media_type": "tv",
            "release_date": show.get("first_air_date"),
            "poster_path": show.get("poster_path"),
        }
    return None