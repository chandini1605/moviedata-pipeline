
from pathlib import Path
import pandas as pd

from src.extract import extract_data
from src.transform import transform_data
from src.load import load_data


# Get project directory
project_dir = Path(__file__).resolve().parent


def run_pipeline():

    print("\n===================================")
    print("       MOVIE DATA PIPELINE")
    print("===================================")

    try:

        # STEP 1: EXTRACT
        print("\nSTEP 1: Extracting data...")

        movies, ratings = extract_data()

        print("Movies extracted:", len(movies))
        print("Ratings extracted:", len(ratings))


        # STEP 2: TRANSFORM
        print("\nSTEP 2: Transforming data...")

        movies, ratings = transform_data(
            movies,
            ratings
        )

        print("Movies transformed:", len(movies))
        print("Ratings transformed:", len(ratings))


        # STEP 3: OMDb ENRICHMENT
        print("\nSTEP 3: Loading OMDb enrichment data...")

        enriched_path = (
            project_dir / "data" / "omdb_enriched.csv"
        )

        if not enriched_path.exists():
            raise FileNotFoundError(
                "OMDb enriched file not found!"
            )

        enriched_movies = pd.read_csv(enriched_path)

        print("OMDb records loaded:", len(enriched_movies))


        # STEP 4: LOAD
        print("\nSTEP 4: Loading data into MySQL...")

        load_data(
            movies,
            ratings,
            enriched_movies
        )


        # COMPLETED
        print("\n===================================")
        print("  MOVIE DATA PIPELINE COMPLETED!")
        print("===================================")

    except Exception as error:

        print("\nPipeline failed!")
        print("Error:", error)


if __name__ == "__main__":
    run_pipeline()