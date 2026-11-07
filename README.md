# Movie Data Pipeline

An end-to-end data engineering project that extracts movie and rating data from the **MovieLens Small** dataset, transforms it using Python, enriches movie details through the **OMDb API**, and loads the results into a relational **MySQL** database for SQL analysis.

## 1. Project Overview

The project uses two MovieLens files:

- `movies.csv` — movie ID, title and genres.
- `ratings.csv` — user ID, movie ID, rating and timestamp.

The data is explored, transformed, enriched with additional movie information where available, and stored in MySQL. SQL queries are then used to answer the assignment questions.

## 2. ETL Architecture

![ETL architecture diagram](docs/images/etl_architecture.png)

### Extract — `src/extract.py`
Reads `movies.csv` and `ratings.csv` from the `data/` directory. It checks that both files exist before loading them into Pandas DataFrames.

### Transform — `src/transform.py`
- Converts Unix timestamps into readable datetime values.
- Extracts a four-digit release year from movie titles when available.
- Splits pipe-separated genre values into individual genres.

Titles without a standard year in parentheses remain without a release year rather than being assigned an assumed value.

### Enrich — `src/enrich.py` and `src/batch_enrich.py`
Calls the OMDb API using a movie title and, when available, its year. It collects details such as director, actors, plot, release date, runtime, genre, language, country, box office, IMDb rating and awards. Batch results are saved in `data/omdb_enriched.csv`.

**Recorded batch result:** 990 movies were processed; OMDb found 633 and did not find 357. Unmatched records are retained in the enrichment output.

### Load — `src/load.py`
Connects to MySQL and loads movie, rating, genre and movie-to-genre records. `INSERT IGNORE` is used to avoid duplicate primary-key records when loading data again.

### Orchestration — `etl.py`
Runs the main sequence: extract MovieLens data, transform it, read the saved OMDb enrichment CSV, and load the data into MySQL. The OMDb batch enrichment step is run separately before this orchestration script.

## 3. Dataset and EDA Highlights

| Dataset | Records | Columns |
|---|---:|---:|
| `movies.csv` | 9,742 | 3 |
| `ratings.csv` | 100,836 | 4 |

Recorded EDA findings:
- No missing values were identified in the original CSV files.
- No duplicate movie records or duplicate `(userId, movieId)` rating pairs were identified.
- The average source rating is approximately **3.50**.
- 13 movie titles did not contain a standard four-digit year in parentheses.

## 4. MySQL Database Design

![MySQL schema and relationships](docs/images/database_schema.png)

The database contains four tables:

| Table | Purpose | Keys |
|---|---|---|
| `movies` | MovieLens movie information and available OMDb details | `movie_id` primary key |
| `ratings` | User ratings for movies | Composite primary key (`user_id`, `movie_id`); `movie_id` is a foreign key |
| `genres` | Unique genre names | `genre_id` primary key; `genre_name` unique |
| `movie_genres` | Maps movies to their genres | Composite primary key (`movie_id`, `genre_id`); both columns are foreign keys |

### Relationships explained

- **movies → ratings (one-to-many):** one movie can have ratings from many users; each rating refers to one movie.
- **movies → movie_genres (one-to-many):** a movie can have several genre links.
- **genres → movie_genres (one-to-many):** a genre can be linked to many movies.
- **movies ↔ genres (many-to-many):** a movie can have multiple genres and a genre can belong to multiple movies. `movie_genres` is the junction table that implements this relationship.

The `ratings` table uses `(user_id, movie_id)` as its composite primary key.

### Recorded database row counts

| Table | Records |
|---|---:|
| `movies` | 9,742 |
| `ratings` | 100,836 |
| `genres` | 19 |
| `movie_genres` | 22,050 |

## 5. SQL Analysis

`queries.sql` contains queries to:
1. Find the movie with the highest average rating.
2. Find the top five genres by average rating.
3. Find the director with the most movies.
4. Calculate average ratings by release year.

## 6. Project Structure

```text
moviedata-pipeline/
├── data/
│   ├── movies.csv
│   ├── ratings.csv
│   └── omdb_enriched.csv
├── docs/
│   └── images/
│       ├── etl_architecture.png
│       └── database_schema.png
├── eda/
│   └── data_exploration.ipynb
├── src/
│   ├── __init__.py
│   ├── extract.py
│   ├── transform.py
│   ├── enrich.py
│   ├── batch_enrich.py
│   └── load.py
├── tests/
├── etl.py
├── schema.sql
├── queries.sql
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## 7. Technologies Used

- Python and Pandas — extraction and transformation.
- Requests — OMDb API calls.
- python-dotenv — environment variable configuration.
- MySQL and mysql-connector-python — relational storage and database connectivity.
- Jupyter Notebook — exploratory data analysis.
- SQL — analytical queries.
- Git and GitHub — version control.

## 8. Setup and Run

### 1. Clone the repository

```bash
git clone https://github.com/chandini1605/moviedata-pipeline.git
cd moviedata-pipeline
```

### 2. Create and activate a virtual environment (Windows)

```bash
python -m venv venv
venv\\Scripts\\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure `.env`

Create `.env` in the project root and add your own credentials:

```env
OMDB_API_KEY=your_omdb_api_key
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
```

Do not commit `.env` or expose API keys and passwords. Ensure `.env` is listed in `.gitignore`.

### 5. Create database tables

Open `schema.sql` in MySQL Workbench and execute it. This creates the `movie_analytics` database and its four tables.

### 6. Run OMDb batch enrichment

```bash
python -m src.batch_enrich
```

The OMDb API has a daily request limit. The batch script may need to be run more than once if it is configured to process a limited number of records per run.

### 7. Run the ETL pipeline

```bash
python etl.py
```

### 8. Run SQL queries

Open `queries.sql` in MySQL Workbench and execute the queries.

## 9. Data Quality and Rerun Behaviour

- The extraction step checks that the source files exist.
- Missing release years are not guessed.
- Movies not found by OMDb are retained in the enrichment output.
- Primary and foreign keys enforce database relationships.
- `INSERT IGNORE` helps prevent duplicate records on subsequent loads.

## 10. Key Outcomes

- Developed a modular Python ETL workflow.
- Integrated an external API for movie enrichment.
- Designed a relational MySQL database with four tables.
- Implemented primary keys, foreign keys and a junction table.
- Loaded 9,742 movies and 100,836 ratings.
- Prepared SQL analysis for movies, genres, directors and release years.

## 11. Future Improvements

- Add incremental loading for new or changed records.
- Add structured logging and detailed error reporting.
- Introduce automated data-quality checks.
- Improve API retry and rate-limit handling.
- Build a Power BI dashboard from the MySQL data.

## Author

**Chandini Reddy**  
GitHub: https://github.com/chandini1605  
Repository: https://github.com/chandini1605/moviedata-pipeline


