import pandas as pd
from pathlib import Path

def extract_data():

    # Get the project directory
    project_dir = Path(__file__).resolve().parent.parent



    # Locate the CSV files
    movies_path = project_dir / "data" / "movies.csv"
    ratings_path = project_dir / "data" / "ratings.csv"


        # Check whether the files exist
    if not movies_path.exists():
        raise FileNotFoundError(f"Movies file not found: {movies_path}")

    if not ratings_path.exists():
        raise FileNotFoundError(f"Ratings file not found: {ratings_path}")

    # Read the datasets
    movies = pd.read_csv(movies_path)
    ratings = pd.read_csv(ratings_path)

    print("Datasets extracted successfully!")

    return movies, ratings