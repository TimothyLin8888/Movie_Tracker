import requests
import os
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
from datetime import datetime
import requests

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

imdb_ids = [
    "tt33886806",
    "tt0075148",
    "tt0080684"
]
BASE_DIR = Path(__file__).resolve().parent.parent
csv_file = "C:/Users/timmy/Movie_Tracker/backend/data/IMDbUserRatings.csv"
movies = pd.read_csv(csv_file)

imported = 0
skipped_tv = 0
not_found = 0



for _, row in movies.iterrows():

    imdb_id = row["Title ID"]

    rating = int(row["Rating"])

    watch_date = datetime.fromisoformat(
        row["Last Modified Date"].replace("Z", "+00:00")
    ).date()

    # existing = (
    #     db.query(Movie)
    #     .filter(Movie.imdb_id == imdb_id)
    #     .first()
    # )

    # if existing:
    #     continue

    url = f"https://api.themoviedb.org/3/find/{imdb_id}"

    response = requests.get(
        url,
        params={
            "api_key": TMDB_API_KEY,
            "external_source": "imdb_id"
        }
    )

    # if response.status_code != 200:
    #     print(f"TMDB error for {imdb_id}: {response.status_code}")
    #     print(response.text)

    #     skipped += 1
    #     continue
    # if response.status_code != 200:
    #     skipped += 1
    #     continue

    data = response.json()

    movie_results = data.get("movie_results", [])
    tv_results = data.get("tv_results", [])

    print(f"Movie Results: {movie_results}")
    print(f"Tv Results: {tv_results}")