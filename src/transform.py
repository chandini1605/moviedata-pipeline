import pandas as pd


def transform_data(movies, ratings):

    # Make copies so the original data is not changed
    movies = movies.copy()
    ratings = ratings.copy()

    # Convert Unix timestamp into readable datetime
    ratings["timestamp"] = pd.to_datetime(
        ratings["timestamp"],
        unit="s"
    )

    print("Timestamp converted successfully!")

    # Extract release year from movie title
    movies["release_year"] = movies["title"].str.extract(r"\((\d{4})\)")

    # Convert release year into numeric format
    movies["release_year"] = pd.to_numeric(
        movies["release_year"],
        errors="coerce"
    )

    print("Release year extracted successfully!")


        # Split movie genres into individual genres
    movies["genres"] = movies["genres"].str.split("|")

    print("Genres separated successfully!")

    return movies, ratings