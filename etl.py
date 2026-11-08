
from pathlib import Path
import pandas as pd
import logging

from src.extract import extract_data
from src.transform import transform_data
from src.load import load_data


# Get project directory
project_dir = Path(__file__).resolve().parent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def run_pipeline():

    logger.info("===================================")
    logger.info("       MOVIE DATA PIPELINE")
    logger.info("===================================")

    try:

        # STEP 1: EXTRACT
        logger.info("STEP 1: Extracting data...")

        movies, ratings = extract_data()

        logger.info("Movies extracted: %s", len(movies))
        logger.info("Ratings extracted: %s", len(ratings))


        # STEP 2: TRANSFORM
        logger.info("STEP 2: Transforming data...")

        movies, ratings = transform_data(
            movies,
            ratings
        )

        logger.info("Movies transformed: %s", len(movies))
        logger.info("Ratings transformed: %s", len(ratings))


        # STEP 3: OMDb ENRICHMENT
        logger.info("STEP 3: Loading OMDb enrichment data...")

        enriched_path = (
            project_dir / "data" / "omdb_enriched.csv"
        )

        if not enriched_path.exists():
            raise FileNotFoundError(
                f"OMDb enriched file not found: {enriched_path}"
            )

        enriched_movies = pd.read_csv(enriched_path)

        logger.info(
            "OMDb records loaded: %s",
            len(enriched_movies)
        )


        # STEP 4: LOAD
        logger.info("STEP 4: Loading data into MySQL...")

        load_data(
            movies,
            ratings,
            enriched_movies
        )


        # COMPLETED
        logger.info("===================================")
        logger.info("  MOVIE DATA PIPELINE COMPLETED!")
        logger.info("===================================")

    except Exception:
        logger.exception("Movie data pipeline failed!")
        raise


if __name__ == "__main__":
    run_pipeline()
