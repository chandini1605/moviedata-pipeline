
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from src.extract import extract_data
from src.enrich import (
    enrich_movie,
    OMDbLimitError,
    OMDbAPIKeyError,
    OMDbAPIError,
    get_api_request_count
)


OUTPUT_COLUMNS = [
    "movieId",
    "MovieLensTitle",
    "release_year",
    "OMDbFound",
    "Title",
    "Director",
    "Actors",
    "Plot",
    "Released",
    "Runtime",
    "Genre",
    "Language",
    "Country",
    "BoxOffice",
    "imdbRating",
    "Awards"
]


def batch_enrich_movies():

    project_dir = Path(__file__).resolve().parent.parent

    output_path = project_dir / "data" / "omdb_enriched.csv"

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Extract MovieLens data
    movies, ratings = extract_data()

    print("Datasets extracted successfully!")

    # Preserve previously successful records
    if output_path.exists():

        existing_data = pd.read_csv(output_path)

        if "OMDbFound" not in existing_data.columns:
            raise ValueError(
                "OMDbFound column is missing from the enrichment CSV."
            )

        successful_data = existing_data[
            existing_data["OMDbFound"]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("true")
        ].copy()

        # Create a backup before removing unsuccessful records
        backup_path = output_path.with_name(
            f"omdb_enriched_backup_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )

        shutil.copy2(output_path, backup_path)

        # Keep only successful records
        successful_data = successful_data.reindex(
            columns=OUTPUT_COLUMNS
        )

        successful_data.to_csv(
            output_path,
            index=False
        )

        processed_ids = set(
            pd.to_numeric(
                successful_data["movieId"],
                errors="coerce"
            ).dropna().astype(int)
        )

        print(
            f"Successful records preserved: {len(processed_ids)}"
        )

        print(f"Backup created: {backup_path}")

    else:

        processed_ids = set()

        pd.DataFrame(
            columns=OUTPUT_COLUMNS
        ).to_csv(
            output_path,
            index=False
        )

    # Process remaining movies
    for _, movie in movies.iterrows():

        movie_id = int(movie["movieId"])

        original_title = movie["title"]

        # Skip movies already enriched successfully
        if movie_id in processed_ids:
            continue

        # Extract release year
        year_match = re.search(
            r"\((\d{4})\)\s*$",
            str(original_title)
        )

        year = (
            int(year_match.group(1))
            if year_match
            else None
        )

        try:

            details = enrich_movie(
                original_title,
                year
            )

            if details is None:

                record = {
                    "movieId": movie_id,
                    "MovieLensTitle": original_title,
                    "release_year": year,
                    "OMDbFound": False
                }

            else:

                record = {
                    "movieId": movie_id,
                    "MovieLensTitle": original_title,
                    "release_year": year,
                    "OMDbFound": True,
                    **details
                }

                processed_ids.add(movie_id)

            # Save each result immediately
            pd.DataFrame(
                [record],
                columns=OUTPUT_COLUMNS
            ).to_csv(
                output_path,
                mode="a",
                header=False,
                index=False
            )

            print(
                f"Requests: {get_api_request_count()} | "
                f"Movie: {original_title} | "
                f"Found: {details is not None}"
            )

        except OMDbLimitError as e:

            print(f"API limit error: {e}")
            break

        except OMDbAPIKeyError as e:

            print(f"API key error: {e}")
            break

        except OMDbAPIError as e:

            print(f"OMDb error: {e}")
            break

        except requests.exceptions.RequestException as e:

            print(f"API/network error: {e}")
            break

    print("\nBatch enrichment finished.")

    print(
        f"API requests: {get_api_request_count()}"
    )

    print(
        f"Successful movies: {len(processed_ids)}"
    )

    print(
        f"Output: {output_path}"
    )


if __name__ == "__main__":
    batch_enrich_movies()
