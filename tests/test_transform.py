from src.extract import extract_data
from src.transform import transform_data

# Extract the original datasets
movies, ratings = extract_data()

# Transform the datasets
movies, ratings = transform_data(movies, ratings)

# Check the results
print("\nMovies after transformation:")
print(movies[["title", "release_year", "genres"]].head())

print("\nRatings after transformation:")
print(ratings[["userId", "movieId", "rating", "timestamp"]].head())

print("\nRelease year data type:")
print(movies["release_year"].dtype)

print("\nTimestamp data type:")
print(ratings["timestamp"].dtype)


print("Movies with missing release year:",
      movies["release_year"].isna().sum())


# Check movies without a release year
missing_year_movies = movies[movies["release_year"].isna()]

print("\nMovies without release year:")
print(missing_year_movies[["movieId", "title"]].to_string(index=False))