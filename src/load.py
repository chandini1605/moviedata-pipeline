
import os
from pathlib import Path

import pandas as pd
import mysql.connector
from dotenv import load_dotenv


# Get project directory
project_dir = Path(__file__).resolve().parent.parent

# Load database credentials
load_dotenv(project_dir / ".env")


# Create MySQL connection
def create_connection():

    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD"),
            database="movie_analytics"
        )

        print("Successfully connected to MySQL!")

        return connection

    except mysql.connector.Error as error:
        print("Database connection failed:", error)
        raise


# Convert missing values into None for MySQL
def clean_value(value):

    if pd.isna(value):
        return None

    if isinstance(value, str):

        value = value.strip()

        if value.upper() in ("N/A", "NA", ""):
            return None

        return value

    if hasattr(value, "item"):
        return value.item()

    return value


# Convert runtime text into minutes
def clean_runtime(value):

    value = clean_value(value)

    if value is None:
        return None

    runtime = str(value).lower().replace("min", "").strip()

    runtime = pd.to_numeric(runtime, errors="coerce")

    if pd.isna(runtime):
        return None

    return int(runtime)


# Convert box office text into a numeric amount
def clean_box_office(value):

    value = clean_value(value)

    if value is None:
        return None

    amount = str(value).replace("$", "").replace(",", "").strip()

    amount = pd.to_numeric(amount, errors="coerce")

    if pd.isna(amount):
        return None

    return int(amount)


# Load all four MySQL tables
def load_data(movies, ratings, enriched_movies):

    # Remove duplicate release_year column from OMDb data
    enriched_movies = enriched_movies.drop(
        columns=["release_year"],
        errors="ignore"
    )

    # Merge MovieLens data with OMDb data
    movies = movies.merge(
        enriched_movies,
        on="movieId",
        how="left"
    )

    # Convert OMDb release date
    movies["Released"] = pd.to_datetime(
        movies["Released"],
        format="%d %b %Y",
        errors="coerce"
    ).dt.date

    # Convert IMDb rating into numeric format
    movies["imdbRating"] = pd.to_numeric(
        movies["imdbRating"],
        errors="coerce"
    )

    connection = create_connection()
    cursor = connection.cursor()

    try:

        # -----------------------------------
        # 1. LOAD MOVIES
        # -----------------------------------

        movie_query = """
            INSERT INTO movies (
                movie_id, title, release_year, omdb_found,
                director, actors, plot, released, runtime,
                omdb_genre, language, country, box_office,
                imdb_rating, awards
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                release_year = VALUES(release_year),
                omdb_found = VALUES(omdb_found),
                director = VALUES(director),
                actors = VALUES(actors),
                plot = VALUES(plot),
                released = VALUES(released),
                runtime = VALUES(runtime),
                omdb_genre = VALUES(omdb_genre),
                language = VALUES(language),
                country = VALUES(country),
                box_office = VALUES(box_office),
                imdb_rating = VALUES(imdb_rating),
                awards = VALUES(awards)
        """

        movie_records = []

        for _, row in movies.iterrows():

            found = clean_value(row["OMDbFound"])

            if found is not None:
                found = str(found).strip().lower() in (
                    "true", "1", "yes"
                )

            record = (
                int(row["movieId"]),
                clean_value(row["title"]),
                clean_value(row["release_year"]),
                found,
                clean_value(row["Director"]),
                clean_value(row["Actors"]),
                clean_value(row["Plot"]),
                clean_value(row["Released"]),
                clean_runtime(row["Runtime"]),
                clean_value(row["Genre"]),
                clean_value(row["Language"]),
                clean_value(row["Country"]),
                clean_box_office(row["BoxOffice"]),
                clean_value(row["imdbRating"]),
                clean_value(row["Awards"])
            )

            movie_records.append(record)

        cursor.executemany(movie_query, movie_records)

        print("Movies processed:", len(movie_records))
        print("Movie rows inserted/updated:", cursor.rowcount)


        # -----------------------------------
        # 2. LOAD RATINGS
        # -----------------------------------

        ratings_query = """
            INSERT INTO ratings (
                user_id, movie_id, rating, timestamp
            )
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                rating = VALUES(rating),
                timestamp = VALUES(timestamp)
        """

        rating_records = []

        for row in ratings.itertuples(index=False):

            timestamp = row.timestamp

            if pd.notna(timestamp):
                timestamp = pd.Timestamp(
                    timestamp
                ).to_pydatetime()
            else:
                timestamp = None

            record = (
                int(row.userId),
                int(row.movieId),
                float(row.rating),
                timestamp
            )

            rating_records.append(record)

        cursor.executemany(ratings_query, rating_records)

        print("Ratings processed:", len(rating_records))
        print("Rating rows inserted/updated:", cursor.rowcount)


        # -----------------------------------
        # 3. LOAD GENRES
        # -----------------------------------

        unique_genres = set()

        for genre_list in movies["genres"]:

            if isinstance(genre_list, list):

                for genre in genre_list:

                    if genre != "(no genres listed)" and genre.strip():
                        unique_genres.add(genre.strip())

        genre_query = """
            INSERT INTO genres (genre_name)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE
                genre_name = VALUES(genre_name)
        """

        genre_records = [
            (genre,) for genre in sorted(unique_genres)
        ]

        cursor.executemany(genre_query, genre_records)

        print("Genres processed:", len(genre_records))
        print("Genre rows inserted/updated:", cursor.rowcount)


        # -----------------------------------
        # 4. LOAD MOVIE_GENRES
        # -----------------------------------

        cursor.execute(
            "SELECT genre_id, genre_name FROM genres"
        )

        genre_mapping = {
            genre_name: genre_id
            for genre_id, genre_name in cursor.fetchall()
        }

        movie_genre_records = []

        for _, row in movies.iterrows():

            movie_id = int(row["movieId"])
            genre_list = row["genres"]

            if isinstance(genre_list, list):

                for genre in genre_list:

                    genre_id = genre_mapping.get(genre)

                    if genre_id is not None:
                        movie_genre_records.append(
                            (movie_id, genre_id)
                        )

        movie_genre_query = """
            INSERT INTO movie_genres (
                movie_id, genre_id
            )
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                genre_id = VALUES(genre_id)
        """

        cursor.executemany(
            movie_genre_query,
            movie_genre_records
        )

        print(
            "Movie-genre relationships processed:",
            len(movie_genre_records)
        )

        print(
            "Movie-genre relationships inserted/updated:",
            cursor.rowcount
        )


        # Save all changes
        connection.commit()

        print("\nAll four tables loaded successfully!")

    except Exception as error:

        connection.rollback()

        print("Data loading failed:", error)

        raise

    finally:

        cursor.close()
        connection.close()
