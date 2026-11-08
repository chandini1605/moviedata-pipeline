
import pandas as pd
from pathlib import Path
import requests

from src.extract import extract_data
from src.enrich import (
    enrich_movie,
    OMDbLimitError,
    get_api_request_count
)


def batch_enrich_movies():

    # Get project directory
    project_dir = Path(__file__).resolve().parent.parent

    # Output file path
    output_path = project_dir / "data" / "omdb_enriched.csv"

    # Create data folder if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Extract movies from MovieLens dataset
    movies, ratings = extract_data()

    # Check whether output file already exists
    if output_path.exists():

        existing_data = pd.read_csv(output_path)

        # Get movie IDs that are already processed
        processed_ids = set(existing_data["movieId"])

        print(f"Already processed movies: {len(processed_ids)}")

    else:
        processed_ids = set()

    # Process movies one by one
    for _, movie in movies.iterrows():

        movie_id = movie["movieId"]
        original_title = movie["title"]

        # Skip previously processed movies
        if movie_id in processed_ids:
            continue

        # Extract release year from movie title
        year = pd.to_numeric(
            pd.Series([original_title]).str.extract(
                r"\((\d{4})\)"
            )[0],
            errors="coerce"
        ).iloc[0]

        try:

            # Fetch movie details from OMDb
            # Title cleaning and retry are handled in enrich.py
            details = enrich_movie(original_title, year)

            # Prepare output record
            if details is not None:

                record = {
                    "movieId": movie_id,
                    "MovieLensTitle": original_title,
                    "release_year": year,
                    "OMDbFound": True,
                    **details
                }

            else:

                record = {
                    "movieId": movie_id,
                    "MovieLensTitle": original_title,
                    "release_year": year,
                    "OMDbFound": False
                }

            # Save result immediately
            pd.DataFrame([record]).to_csv(
                output_path,
                mode="a",
                header=not output_path.exists(),
                index=False
            )

            # Mark movie as processed
            processed_ids.add(movie_id)

            print(
                f"API requests: {get_api_request_count()} | "
                f"Processed: {original_title}"
            )

        except OMDbLimitError as error:

            print(f"\nOMDb daily limit reached: {error}")
            print("Stopping batch enrichment.")
            break

        except requests.exceptions.RequestException as error:

            print(f"\nAPI/network error: {error}")
            print("Stopping batch to avoid further failed requests.")
            break

    print("\nBatch enrichment completed!")
    print(f"Actual API requests made: {get_api_request_count()}")
    print(f"Total movies processed: {len(processed_ids)}")
    print(f"Enriched data saved at: {output_path}")


if __name__ == "__main__":
    batch_enrich_movies()
