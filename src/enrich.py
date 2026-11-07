import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")


def enrich_movie(title, year=None):

    if not API_KEY:
        raise ValueError("OMDb API key not found. Check your .env file.")

    # Send request to OMDb API
    url = "https://www.omdbapi.com/"

    params = {
        "apikey": API_KEY,
        "t": title
    }

    # Add release year if available
    if pd.notna(year):
        params["y"] = int(year)

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    movie_data = response.json()

    # Check whether the movie was found
    if movie_data.get("Response") == "False":
        print(f"Movie not found: {title}")
        return None

    # Extract required details
    details = {
        "Title": movie_data.get("Title"),
        "Director": movie_data.get("Director"),
        "Actors": movie_data.get("Actors"),
        "Plot": movie_data.get("Plot"),
        "Released": movie_data.get("Released"),
        "Runtime": movie_data.get("Runtime"),
        "Genre": movie_data.get("Genre"),
        "Language": movie_data.get("Language"),
        "Country": movie_data.get("Country"),
        "BoxOffice": movie_data.get("BoxOffice"),
        "imdbRating": movie_data.get("imdbRating"),
        "Awards": movie_data.get("Awards")
    }

    return details