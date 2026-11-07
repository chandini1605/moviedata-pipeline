import mysql.connector
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from src.extract import extract_data


# Get project directory
project_dir = Path(__file__).resolve().parent.parent

# Load database credentials from .env
load_dotenv(project_dir / ".env")


# --------------------------------------------------
# 1. CREATE MYSQL CONNECTION
# --------------------------------------------------

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
        return None


# --------------------------------------------------
# 2. LOAD MOVIES TABLE
# --------------------------------------------------

def load_movies():

    # Extract MovieLens data
    movies, ratings = extract_data()

    # Read OMDb enriched data
    enriched_path = project_dir / "data" / "omdb_enriched.csv"
    enriched_movies = pd.read_csv(enriched_path)

    # Merge MovieLens and OMDb data
    movies = movies.merge(
        enriched_movies,
        on="movieId",
        how="left"
    )

    # Extract release year from MovieLens title
    movie_year = movies["title"].str.extract(r"\((\d{4})\)")[0]

    movies["release_year"] = pd.to_numeric(
        movie_year,
        errors="coerce"
    ).fillna(movies["release_year"])

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

    if connection is None:
        return

    cursor = connection.cursor()

    query = """
        INSERT IGNORE INTO movies (
            movie_id, title, release_year, omdb_found,
            director, actors, plot, released, runtime,
            omdb_genre, language, country, box_office,
            imdb_rating, awards
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
    """

    records = []

    for _, row in movies.iterrows():

        found = row["OMDbFound"]

        if pd.isna(found):
            found = None
        else:
            found = str(found).strip().lower() in ("true", "1", "yes")

        record = (
            int(row["movieId"]),
            row["title"],
            int(row["release_year"]) if pd.notna(row["release_year"]) else None,
            found,
            row["Director"] if pd.notna(row["Director"]) else None,
            row["Actors"] if pd.notna(row["Actors"]) else None,
            row["Plot"] if pd.notna(row["Plot"]) else None,
            row["Released"] if pd.notna(row["Released"]) else None,
            row["Runtime"] if pd.notna(row["Runtime"]) else None,
            row["Genre"] if pd.notna(row["Genre"]) else None,
            row["Language"] if pd.notna(row["Language"]) else None,
            row["Country"] if pd.notna(row["Country"]) else None,
            row["BoxOffice"] if pd.notna(row["BoxOffice"]) else None,
            float(row["imdbRating"]) if pd.notna(row["imdbRating"]) else None,
            row["Awards"] if pd.notna(row["Awards"]) else None
        )

        records.append(record)

    try:

        cursor.executemany(query, records)
        connection.commit()

        print("\nMovies loaded successfully!")
        print("Total records processed:", len(records))
        print("Records inserted:", cursor.rowcount)

    except mysql.connector.Error as error:

        connection.rollback()
        print("Error loading movies:", error)

    finally:

        cursor.close()
        connection.close()


# --------------------------------------------------
# 3. LOAD RATINGS TABLE
# --------------------------------------------------

def load_ratings():

    # Extract ratings data
    movies, ratings = extract_data()

    # Convert Unix timestamp into datetime
    ratings["timestamp"] = pd.to_datetime(
        ratings["timestamp"],
        unit="s",
        errors="coerce"
    )

    connection = create_connection()

    if connection is None:
        return

    cursor = connection.cursor()

    query = """
        INSERT IGNORE INTO ratings (
            user_id,
            movie_id,
            rating,
            timestamp
        )
        VALUES (%s, %s, %s, %s)
    """

    records = []

    for row in ratings.itertuples(index=False):

        timestamp = (
            row.timestamp.to_pydatetime()
            if pd.notna(row.timestamp)
            else None
        )

        record = (
            int(row.userId),
            int(row.movieId),
            float(row.rating),
            timestamp
        )

        records.append(record)

    try:

        cursor.executemany(query, records)
        connection.commit()

        print("\nRatings loaded successfully!")
        print("Total records processed:", len(records))
        print("Records inserted:", cursor.rowcount)

    except mysql.connector.Error as error:

        connection.rollback()
        print("Error loading ratings:", error)

    finally:

        cursor.close()
        connection.close()


# --------------------------------------------------
# 4. LOAD GENRES TABLE
# --------------------------------------------------

def load_genres():

    # Extract MovieLens data
    movies, ratings = extract_data()

    # Split genres into individual values
    genre_list = movies["genres"].str.split("|").explode()

    # Remove extra spaces
    genre_list = genre_list.str.strip()

    # Remove the MovieLens placeholder for missing genres
    genre_list = genre_list[
        (genre_list != "(no genres listed)") &
        (genre_list != "")
    ]

    # Get unique genres
    unique_genres = sorted(genre_list.dropna().unique())

    connection = create_connection()

    if connection is None:
        return

    cursor = connection.cursor()

    query = """
        INSERT IGNORE INTO genres (genre_name)
        VALUES (%s)
    """

    records = [(genre,) for genre in unique_genres]

    try:

        cursor.executemany(query, records)
        connection.commit()

        print("\nGenres loaded successfully!")
        print("Unique genres processed:", len(records))
        print("Genres inserted:", cursor.rowcount)

    except mysql.connector.Error as error:

        connection.rollback()
        print("Error loading genres:", error)

    finally:

        cursor.close()
        connection.close()


# --------------------------------------------------
# 5. LOAD MOVIE_GENRES TABLE
# --------------------------------------------------

def load_movie_genres():

    # Extract MovieLens data
    movies, ratings = extract_data()

    # Split movie genres
    movies["genres"] = movies["genres"].str.split("|")

    # Create MySQL connection
    connection = create_connection()

    if connection is None:
        return

    cursor = connection.cursor()

    try:

        # Get genre names and their IDs
        cursor.execute("SELECT genre_id, genre_name FROM genres")

        genre_mapping = {
            genre_name: genre_id
            for genre_id, genre_name in cursor.fetchall()
        }

        # Prepare movie and genre relationships
        records = []

        for _, row in movies.iterrows():

            movie_id = int(row["movieId"])

            for genre in row["genres"]:

                if genre == "(no genres listed)":
                    continue

                genre_id = genre_mapping.get(genre)

                if genre_id is not None:
                    records.append((movie_id, genre_id))

        query = """
            INSERT IGNORE INTO movie_genres (
                movie_id,
                genre_id
            )
            VALUES (%s, %s)
        """

        cursor.executemany(query, records)

        connection.commit()

        print("\nMovie genres loaded successfully!")
        print("Relationships processed:", len(records))
        print("Relationships inserted:", cursor.rowcount)

    except mysql.connector.Error as error:

        connection.rollback()
        print("Error loading movie genres:", error)

    finally:

        cursor.close()
        connection.close()


# --------------------------------------------------
# 6. RUN COMPLETE DATA LOADING PROCESS
# --------------------------------------------------

if __name__ == "__main__":

    print("\nStarting Movie Data Pipeline...")

    load_movies()

    load_ratings()

    load_genres()

    load_movie_genres()

    print("\nMovie Data Pipeline completed!")