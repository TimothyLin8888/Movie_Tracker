from fastapi import APIRouter
from dotenv import load_dotenv
import os
import requests


router = APIRouter(
    prefix="/search"
)
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3/search"

@router.get("/movie")
def search_movie(query: str):
    params = {
        "api_key": TMDB_API_KEY,
        "query": query
    }
    response = requests.get(BASE_URL + "/movie", params=params)
    movie_list = []
    if response.status_code == 200:
        for movie in response.json().get("results", []):
            movie_title = movie.get("title", "No title found")
            movie_id = movie.get("id", "No ID found")
            movie_poster = movie.get("poster_path", "No poster found")
            movie_release_date = movie.get("release_date", "No release date found")
            movie_category = movie.get("original_language", "Movie")
            movie_overview = movie.get("overview", "")
            movie_list.append({
                "title": movie_title,
                "id": movie_id,
                "poster": movie_poster,
                "date": movie_release_date,
                "category": movie_category,
                "description": movie_overview,
            })
        return movie_list
    else:
        return {"error": "Failed to fetch data from TMDB API"}
    

@router.get("/tv")
def search_tv(query: str):
    params = {
        "api_key": TMDB_API_KEY,
        "query": query
    }
    response = requests.get(BASE_URL + "/tv" , params=params)
    tv_list = []
    if response.status_code == 200:
        for tv in response.json().get("results", []):
            tv_title = tv.get("name", "No title found")
            tv_id = tv.get("id", "No ID found")
            tv_poster = tv.get("poster_path", "No poster found")
            tv_release_date = tv.get("first_air_date", "No release date found")
            tv_category = tv.get("original_language", "Movie")
            tv_overview = tv.get("overview", "")
            tv_list.append({
                "title": tv_title,
                "id": tv_id,
                "poster": tv_poster,
                "date": tv_release_date,
                "category": tv_category,
                "description": tv_overview,
            })
        return tv_list
    else:
        return {"error": "Failed to fetch data from TMDB API"}