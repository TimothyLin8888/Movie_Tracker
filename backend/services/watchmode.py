import os

import requests

WATCHMODE_API_KEY = os.getenv("WATCHMODE_API_KEY")
BASE_URL = "https://api.watchmode.com/v1"


def _search(search_field: str, search_value: str, year: int | None = None) -> dict | None:
    params = {
        "apiKey": WATCHMODE_API_KEY,
        "search_field": search_field,
        "search_value": search_value,
        "types": "movie",
    }
    try:
        response = requests.get(f"{BASE_URL}/search/", params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return None

    results = response.json().get("title_results", [])
    if not results:
        return None

    if year:
        for result in results:
            if result.get("year") == year:
                return result

    return results[0]


def resolve_watchmode_id(movie) -> int | None:
    """Look up a Movie's Watchmode title id, preferring the IMDb id when we have one."""
    if movie.imdb_id:
        result = _search("imdb_id", movie.imdb_id)
        if result:
            return result["id"]

    if movie.title:
        year = movie.release_date.year if movie.release_date else None
        result = _search("name", movie.title, year=year)
        if result:
            return result["id"]

    return None


def fetch_sources(watchmode_id: int) -> list[dict]:
    """Return the raw list of streaming sources Watchmode has for a title (empty list on any failure)."""
    if not watchmode_id:
        return []

    url = f"{BASE_URL}/title/{watchmode_id}/sources/"
    params = {"apiKey": WATCHMODE_API_KEY, "regions": "US"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    sources = response.json()
    return sources if isinstance(sources, list) else []
