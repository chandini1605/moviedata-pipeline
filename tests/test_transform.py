import pandas as pd
from src.transform import transform_data


def make_sample():
    movies = pd.DataFrame({
        "movieId": [1, 2, 3],
        "title": ["Toy Story (1995)", "Heat (1995)", "No Year Movie"],
        "genres": ["Adventure|Animation|Comedy", "Action|Crime", "(no genres listed)"],
    })
    ratings = pd.DataFrame({
        "userId": [1, 1],
        "movieId": [1, 2],
        "rating": [4.0, 5.0],
        "timestamp": [964982703, 964981247],
    })
    return movies, ratings


def test_release_year_is_extracted():
    movies, ratings = make_sample()
    movies, _ = transform_data(movies, ratings)
    assert movies.loc[0, "release_year"] == 1995
    assert movies.loc[1, "release_year"] == 1995


def test_missing_year_becomes_null():
    movies, ratings = make_sample()
    movies, _ = transform_data(movies, ratings)
    assert pd.isna(movies.loc[2, "release_year"])


def test_genres_are_split_into_list():
    movies, ratings = make_sample()
    movies, _ = transform_data(movies, ratings)
    assert movies.loc[0, "genres"] == ["Adventure", "Animation", "Comedy"]


def test_timestamp_is_converted_to_datetime():
    movies, ratings = make_sample()
    _, ratings = transform_data(movies, ratings)
    assert pd.api.types.is_datetime64_any_dtype(ratings["timestamp"])


def test_row_counts_do_not_change():
    movies, ratings = make_sample()
    new_movies, new_ratings = transform_data(movies, ratings)
    assert len(new_movies) == 3
    assert len(new_ratings) == 2