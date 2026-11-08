
-- Create database
CREATE DATABASE IF NOT EXISTS movie_analytics;

USE movie_analytics;


-- 1. Movies table
CREATE TABLE IF NOT EXISTS movies (
    movie_id INT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    release_year SMALLINT,

    omdb_found BOOLEAN,

    director VARCHAR(500),
    actors TEXT,
    plot TEXT,
    released DATE,
    runtime SMALLINT,
    omdb_genre VARCHAR(255),
    language VARCHAR(255),
    country VARCHAR(255),
    box_office BIGINT,
    imdb_rating DECIMAL(3,1),
    awards TEXT,

    INDEX idx_movie_year (release_year),
    INDEX idx_movie_director (director),
    INDEX idx_movie_rating (imdb_rating)
);


-- 2. Ratings table
CREATE TABLE IF NOT EXISTS ratings (
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    rating DECIMAL(2,1) NOT NULL,
    timestamp DATETIME,

    PRIMARY KEY (user_id, movie_id),

    FOREIGN KEY (movie_id)
        REFERENCES movies(movie_id),

    INDEX idx_ratings_movie (movie_id),
    INDEX idx_ratings_rating (rating)
);


-- 3. Genres table
CREATE TABLE IF NOT EXISTS genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(100) NOT NULL UNIQUE
);


-- 4. Movie_Genres mapping table
CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INT NOT NULL,
    genre_id INT NOT NULL,

    PRIMARY KEY (movie_id, genre_id),

    FOREIGN KEY (movie_id)
        REFERENCES movies(movie_id),

    FOREIGN KEY (genre_id)
        REFERENCES genres(genre_id),

    INDEX idx_movie_genres_genre (genre_id)
);
