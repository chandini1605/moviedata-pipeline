
USE movie_analytics;


-- Q1. Find the movie with the highest average rating

SELECT
    m.title,
    ROUND(AVG(r.rating), 2) AS average_rating
FROM movies m
INNER JOIN ratings r
    ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title
ORDER BY average_rating DESC
LIMIT 1;


-- Q2. Find the top 5 genres by average rating

SELECT
    g.genre_name,
    ROUND(AVG(r.rating), 2) AS average_rating
FROM genres g
INNER JOIN movie_genres mg
    ON g.genre_id = mg.genre_id
INNER JOIN ratings r
    ON mg.movie_id = r.movie_id
GROUP BY g.genre_id, g.genre_name
ORDER BY average_rating DESC
LIMIT 5;


-- Q3. Find the director with the most movies

SELECT
    director,
    COUNT(*) AS total_movies
FROM movies
WHERE director IS NOT NULL
  AND director <> 'N/A'
GROUP BY director
ORDER BY total_movies DESC
LIMIT 1;


-- Q4. Find the average rating by release year

SELECT
    m.release_year,
    ROUND(AVG(r.rating), 2) AS average_rating
FROM movies m
INNER JOIN ratings r
    ON m.movie_id = r.movie_id
WHERE m.release_year IS NOT NULL
GROUP BY m.release_year
ORDER BY m.release_year;
