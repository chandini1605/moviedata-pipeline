from src.extract import extract_data

# Extract both datasets
movies, ratings = extract_data()

# Display dataset information
print("Movies shape:", movies.shape)
print("Ratings shape:", ratings.shape)

print("\nMovies preview:")
print(movies.head())

print("\nRatings preview:")
print(ratings.head())