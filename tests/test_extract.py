from src.extract import extract_data


def test_extract_returns_data():
    movies, ratings = extract_data()
    assert len(movies) > 0
    assert len(ratings) > 0


def test_expected_columns_exist():
    movies, ratings = extract_data()
    assert {"movieId", "title", "genres"} <= set(movies.columns)
    assert {"userId", "movieId", "rating", "timestamp"} <= set(ratings.columns)