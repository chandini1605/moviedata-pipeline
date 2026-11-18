from src.enrich import enrich_movie

# Test with one movie
movie = enrich_movie("Toy Story", 1995)

print("\nOMDb Movie Details:")
print(movie)