
import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")

# Maximum actual API requests allowed
API_REQUEST_LIMIT = 980
api_requests_made = 0


class OMDbLimitError(Exception):
    pass


def get_api_request_count():
    return api_requests_made


def clean_movie_title(title):

    # Remove release year
    title = re.sub(r"\s*\(\d{4}\)\s*$", "", title)

    # Remove alternate titles
    title = re.sub(r"\s*\([^)]*\)", "", title).strip()

    # Move articles to the beginning
    match = re.match(
        r"^(.*),\s*(The|A|An)$",
        title,
        re.IGNORECASE
    )

    if match:
        title = match.group(2) + " " + match.group(1)

    return title.strip()


def make_api_request(params):

    global api_requests_made

    if api_requests_made >= API_REQUEST_LIMIT:
        raise OMDbLimitError("OMDb request limit reached.")

    # Count every attempted API request
    api_requests_made += 1

    response = requests.get(
        "https://www.omdbapi.com/",
        params=params,
        timeout=10
    )

    response.raise_for_status()

    movie_data = response.json()

    # Check daily API limit
    if movie_data.get("Response") == "False":

        error = movie_data.get("Error", "")

        if "limit" in error.lower():
            raise OMDbLimitError(error)

    return movie_data


def enrich_movie(title, year=None):

    if not API_KEY:
        raise ValueError(
            "OMDb API key not found. Check your .env file."
        )

    # Clean title before API request
    cleaned_title = clean_movie_title(title)

    params = {
        "apikey": API_KEY,
        "t": cleaned_title
    }

    # Add release year if available
    if pd.notna(year):
        params["y"] = int(year)

    # First API request
    movie_data = make_api_request(params)

    # Retry without year if movie is not found
    if movie_data.get("Response") == "False" and "y" in params:

        params.pop("y")
        movie_data = make_api_request(params)

    # Movie not found
    if movie_data.get("Response") == "False":
        print(f"Movie not found: {title}")
        return None

    # Extract movie details
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
