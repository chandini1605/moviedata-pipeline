
USE movie_analytics;


-- Q1. Find the movie with the highest average rating

SELECT
    m.movie_id,
    m.title,
    ROUND(AVG(r.rating), 2) AS average_rating,
    COUNT(DISTINCT r.user_id) AS total_users
FROM movies m
INNER JOIN ratings r
    ON m.movie_id = r.movie_id
GROUP BY
    m.movie_id,
    m.title
HAVING COUNT(DISTINCT r.user_id) >= 10
ORDER BY
    average_rating DESC,
    total_users DESC,
    m.title ASC
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

-- Q3. Director with the most movies (multi-director movies counted for each director)

WITH RECURSIVE director_split AS (

    -- Take the first director from each movie
    SELECT
        movie_id,
        TRIM(SUBSTRING_INDEX(director, ',', 1)) AS director_name,
        CASE
            WHEN INSTR(director, ',') > 0
            THEN TRIM(SUBSTRING(director, INSTR(director, ',') + 1))
            ELSE NULL
        END AS remaining_directors
    FROM movies
    WHERE director IS NOT NULL

    UNION ALL

    -- Take the next director from what's left
    SELECT
        movie_id,
        TRIM(SUBSTRING_INDEX(remaining_directors, ',', 1)),
        CASE
            WHEN INSTR(remaining_directors, ',') > 0
            THEN TRIM(SUBSTRING(remaining_directors, INSTR(remaining_directors, ',') + 1))
            ELSE NULL
        END
    FROM director_split
    WHERE remaining_directors IS NOT NULL
      AND remaining_directors <> ''
)

SELECT
    director_name,
    COUNT(DISTINCT movie_id) AS total_movies
FROM director_split
WHERE director_name <> ''
  AND UPPER(director_name) <> 'N/A'
GROUP BY director_name
ORDER BY total_movies DESC, director_name ASC
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
