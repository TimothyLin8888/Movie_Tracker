import httpx
import os

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

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