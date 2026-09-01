from fastapi import APIRouter, UploadFile, File, HTTPException
from services.tmdb import lookup_imdb_id
import csv
import asyncio
import io

router = APIRouter()

@router.post("/imdb")
async def import_imdb(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    movies = []
    tv_shows = []
    failed = []

    for row in reader:
        imdb_id = row["Title ID"]
        rating = int(row["Rating"])
        rated_date = row["Last Modified Date"]

        result = await lookup_imdb_id(imdb_id)

        if result is None:
            failed.append(imdb_id)
            await asyncio.sleep(0.1)
            continue

        result["user_rating"] = rating
        result["rated_date"] = rated_date

        if result["media_type"] == "movie":
            movies.append(result)
        else:
            tv_shows.append(result)

        await asyncio.sleep(0.1)

    return {
        "movies_imported": len(movies),
        "tv_imported": len(tv_shows),
        "failed_count": len(failed),
        "failed_ids": failed,
        "movies": movies,
        "tv": tv_shows,
    }