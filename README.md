# Movie Data Pipeline

This pipeline reads the MovieLens small dataset (movies and ratings), pulls extra details for each movie from the OMDb API, cleans everything up in Python, loads it into MySQL, and then answers four questions with SQL.

## What it does

1. Reads `movies.csv` and `ratings.csv` from the `data/` folder.
2. Looks up each movie on OMDb (director, actors, plot, runtime, box office, IMDb rating, awards) and saves the results to `data/omdb_enriched.csv`.
3. Cleans the data: converts timestamps, pulls the release year out of the title, splits the genres, turns runtime and box office into numbers.
4. Loads four tables into MySQL.
5. `queries.sql` answers the analysis questions.

The dataset has 9,742 movies and 100,836 ratings.

![ETL architecture](https://github.com/user-attachments/assets/72339ad5-4f92-4caa-9a78-03891efa5af9)

## Folder layout

```text
moviedata-pipeline/
├── data/                   movies.csv, ratings.csv, omdb_enriched.csv
├── eda/                    notebook where I explored the data first
├── src/
│   ├── extract.py          reads the CSV files
│   ├── transform.py        timestamps, release year, genre splitting
│   ├── enrich.py           OMDb lookup, title cleaning, API error handling
│   ├── batch_enrich.py     runs the lookups in batches and saves as it goes
│   └── load.py             cleans OMDb values and writes everything to MySQL
├── tests/
├── etl.py                  main script
├── schema.sql              table definitions
├── queries.sql             the four analysis queries
├── requirements.txt
├── .env.example            copy this to .env and fill in your values
└── README.md
```

## How to run it

You need Python 3.10 or newer, MySQL 8, and a free OMDb API key (https://www.omdbapi.com/apikey.aspx).

```bash
git clone https://github.com/chandini1605/moviedata-pipeline.git
cd moviedata-pipeline

python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then open .env and fill in your details
```

Your `.env` should look like this:

```env
OMDB_API_KEY=your_omdb_api_key
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
```

The `.env` file is in `.gitignore`, so it never gets committed.

Then run these in order:

```bash
mysql -u root -p < schema.sql        # creates the database and tables
python -m src.batch_enrich           # fetches OMDb data (see note below)
python etl.py                        # transforms and loads everything
mysql -u root -p < queries.sql       # runs the analysis queries
```

If you already created the tables with an older version of `schema.sql`, drop the `movie_analytics` database first. `CREATE TABLE IF NOT EXISTS` won't change the column types of tables that already exist.

You can run `etl.py` as many times as you like. It updates existing rows instead of creating duplicates.

A note on the OMDb step: the free API key only allows about 1,000 requests a day, and there are nearly 10,000 movies. So `batch_enrich.py` stops after 980 requests and picks up where it left off the next time. Run it once a day until the enrichment file covers all the movies.

## Database design

![Database schema](https://github.com/user-attachments/assets/fb3e9046-bd2e-43ce-973d-9bc1da97f3c6)

There are four tables:

- **movies**: one row per movie, with the MovieLens fields plus whatever OMDb gave back. There is an `omdb_found` column so I can tell which movies were matched.
- **ratings**: one row per user rating. The primary key is (`user_id`, `movie_id`), and `movie_id` points to `movies`.
- **genres**: one row per genre name.
- **movie_genres**: links movies to genres.

The main thing I thought about was genres. In the CSV they come as one string like `Adventure|Animation|Comedy`, which is awkward to query. A movie can have many genres and a genre belongs to many movies, so I used a separate `genres` table and a link table between the two. That makes "average rating per genre" a normal join. Ratings got their own table because one movie has lots of ratings. The OMDb details stay on `movies` because each movie has only one set of them.

I also added indexes on the columns the queries filter and join on (`release_year`, `director`, `movie_id` and `genre_id` in the link tables, and `rating`).

Row counts after loading: movies 9,742, ratings 100,836, genres 19, movie_genres 22,050.

## How I handled messy data

- **Release year:** taken from the end of the title, e.g. `Toy Story (1995)`. 13 titles have no year, so those are left empty. I didn't want to guess.
- **Genres:** 34 movies have `(no genres listed)`. I didn't store that as a real genre.
- **Timestamps:** the Unix numbers in `ratings.csv` are converted to proper dates.
- **Runtime and box office:** OMDb sends these as text like `81 min` and `$229,947,062`. They are converted to whole numbers (minutes and dollars) before loading.
- **Missing OMDb values:** blanks and `N/A` become NULL. Dates and IMDb ratings are converted to proper types, and anything that can't be converted also becomes NULL.
- **Movie not found on OMDb:** the movie is still kept, with `omdb_found` set to false, so its ratings and genres still count in the analysis.
- **API problems:** an invalid key, a daily-limit message, or any unexpected OMDb error stops the batch straight away with a clear message. Only a plain "Movie not found" counts as a miss. Everything fetched so far is already saved.
- **Reruns:** the load uses `INSERT ... ON DUPLICATE KEY UPDATE` inside one transaction, so a rerun updates changed rows, never duplicates them, and a failed load rolls back cleanly.
- **Logging:** `etl.py` logs each step and re-raises any error, so a failed run doesn't look like a success.

## The analysis queries

`queries.sql` answers:

1. **Highest average rating.** Only movies with at least 10 ratings are counted, because a movie with a single 5-star rating shouldn't win. Ties are broken by number of ratings, then by title.
2. **Top 5 genres by average rating.**
3. **Director with the most movies.** Some movies have several directors in one text field, so a recursive query splits them and each director is counted separately.
4. **Average rating for each release year.**

Q3 only covers movies that OMDb has matched, so the answer depends on how much of the dataset has been enriched.

## Choices and assumptions

- I picked MySQL because it's close to what a real team would use, with foreign keys and transactions.
- I kept the OMDb step separate from the load step. Because of the daily limit, I save every API response to a CSV, so I can re-run the load as often as I want without using up any API calls.
- I searched OMDb by title and year, since MovieLens `movies.csv` has no IMDb IDs. They are in `links.csv`, but the assignment only asks for two files.
- I assumed the year in brackets at the end of a title is the release year, and that each user rates a movie only once. The notebook confirms there are no duplicate (user, movie) pairs.

## Problems I ran into

**The API limit.** I couldn't fetch all 9,742 movies in one go. The script saves each result straight away, skips movies it has already fetched, and stops cleanly when the limit is hit, so I can run it day after day.

**Titles that don't match.** MovieLens writes titles like `Usual Suspects, The (1995)` or `Seven (a.k.a. Se7en) (1995)`, and OMDb doesn't recognise those. My first batch of 990 movies found only 633 on OMDb. Looking at the misses, around 280 were caused by this title format and not by missing movies. I fixed it by moving "The/A/An" back to the front, removing the alternate-title brackets, and retrying without the year if the first search fails. After that, 876 of the next 887 movies were found. The old misses are removed from the file and fetched again.

**Silent failures.** At first, a bad API key or a failed database connection could still end with a "pipeline completed" message. Now those errors stop the run.

**Multiple directors in one field.** About 5% of matched movies list two or more directors. Counting the whole text as one director gave wrong answers for Q3, so the query now splits them.

## Limitations

- Not every movie has been enriched yet. At the last run the enrichment file covered about 15% of the movies, so director results are based on that part of the data. Each daily run adds up to 980 more.
- Directors and actors are still stored as plain text on `movies`. A separate `directors` table (like `genres`) would be cleaner.
- Movies that OMDb really doesn't have are tried again on every batch run, which uses up some of the daily quota.
- The tests in `tests/` are simple check scripts, not automated tests with assertions.

## What I'd do next

- Use the IMDb IDs from `links.csv` for exact matching instead of searching by title.
- Add `directors` and `movie_directors` tables, the same way I did for genres.
- Remember which movies OMDb really doesn't have, so they aren't requested again.
- Add a decade column and rating counts per movie.
- Turn the check scripts into real `pytest` tests.
- For a real production setup: schedule the job with something like Airflow, call the API with retries and rate limiting, bulk load the ratings, add data-quality checks, and use Docker so setup is the same everywhere.

## Author

Chandini, https://github.com/chandini1605
