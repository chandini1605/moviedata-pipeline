
import pandas as pd
from pathlib import Path
import requests

from src.extract import extract_data
from src.enrich import enrich_movie


# Maximum number of API requests in this batch
MAX_API_CALLS = 985


def batch_enrich_movies():

    # Get project directory
    project_dir = Path(__file__).resolve().parent.parent

    # Output file path
    output_path = project_dir / "data" / "omdb_enriched.csv"

    # Extract movies from MovieLens dataset
    movies, ratings = extract_data()

    # Check whether an output file already exists
    if output_path.exists():

        existing_data = pd.read_csv(output_path)

        # Get movie IDs that are already processed
        processed_ids = set(existing_data["movieId"])

        print(f"Already processed movies: {len(processed_ids)}")

    else:
        processed_ids = set()

    # Count new API requests
    api_calls = 0

    # Process movies one by one
    for _, movie in movies.iterrows():

        # Stop after reaching the API request limit
        if api_calls >= MAX_API_CALLS:
            print("\nAPI request limit reached.")
            break

        movie_id = movie["movieId"]
        original_title = movie["title"]

        # Skip movies that are already processed
        if movie_id in processed_ids:
            continue

        # Extract release year from movie title
        year = pd.to_numeric(
            pd.Series([original_title]).str.extract(r"\((\d{4})\)")[0],
            errors="coerce"
        ).iloc[0]

        # Remove release year from movie title
        title = pd.Series([original_title]).str.replace(
            r"\s*\(\d{4}\)$",
            "",
            regex=True
        ).iloc[0]

        try:

            # Fetch movie details from OMDb
            details = enrich_movie(title, year)

            # Count this API request, including movies not found
            api_calls += 1

            # Prepare the output record
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

            # Save the result immediately
            pd.DataFrame([record]).to_csv(
                output_path,
                mode="a",
                header=not output_path.exists(),
                index=False
            )

            # Mark this movie as processed
            processed_ids.add(movie_id)

            print(
                f"{api_calls}/{MAX_API_CALLS} - "
                f"Processed: {original_title}"
            )

        except requests.exceptions.RequestException as error:

            print(f"\nAPI/network error: {error}")
            print("Stopping the batch to avoid further failed requests.")
            break

    print("\nBatch enrichment completed!")
    print(f"API requests made in this batch: {api_calls}")
    print(f"Enriched data saved at: {output_path}")


if __name__ == "__main__":
    batch_enrich_movies()