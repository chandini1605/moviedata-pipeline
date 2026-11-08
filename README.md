# Movie Data Pipeline

This pipeline reads the MovieLens small dataset (movies and ratings), pulls extra details for each movie from the OMDb API, cleans everything up in Python, loads it into MySQL, and then answers four questions with SQL.

## What it does

1. Reads `movies.csv` and `ratings.csv` from the `data/` folder.
2. Looks up each movie on OMDb (director, actors, plot, runtime, box office, IMDb rating, awards) and saves the results to `data/omdb_enriched.csv`.
3. Cleans the data: converts timestamps, pulls the release year out of the title, splits the genres.
4. Loads four tables into MySQL.
5. `queries.sql` answers the analysis questions from the assignment.

The dataset has 9,742 movies and 100,836 ratings.

![ETL architecture](https://github.com/user-attachments/assets/72339ad5-4f92-4caa-9a78-03891efa5af9)

## Folder layout

```text
moviedata-pipeline/
├── data/                   movies.csv, ratings.csv, omdb_enriched.csv
├── eda/                    notebook where I explored the data first
├── src/
│   ├── extract.py          reads the CSV files
│   ├── transform.py        cleaning and genre/year handling
│   ├── enrich.py           one OMDb lookup
│   ├── batch_enrich.py     runs the lookups in batches and saves as it goes
│   └── load.py             writes everything to MySQL
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

You can run `schema.sql` and `etl.py` as many times as you like without getting duplicate rows.

A note on the OMDb step: the free API key only allows about 1,000 requests a day, and there are nearly 10,000 movies. So `batch_enrich.py` stops after a fixed number of calls and remembers what it has already done. Run it again the next day and it carries on where it stopped.

## Database design

![Database schema](https://github.com/user-attachments/assets/fb3e9046-bd2e-43ce-973d-9bc1da97f3c6)

There are four tables:

- **movies**: one row per movie, with the MovieLens fields plus whatever OMDb gave back. There is an `omdb_found` column so I can tell which movies were matched.
- **ratings**: one row per user rating. The primary key is (`user_id`, `movie_id`), and `movie_id` points to `movies`.
- **genres**: one row per genre name.
- **movie_genres**: links movies to genres.

The main thing I thought about was genres. In the CSV they come as one string like `Adventure|Animation|Comedy`, which is awkward to query. A movie can have many genres and a genre belongs to many movies, so I used a separate `genres` table and a link table between the two. That makes "average rating per genre" a normal join. Ratings got their own table because one movie has lots of ratings. The OMDb details stay on `movies` because each movie has only one set of them.

Row counts after loading: movies 9,742, ratings 100,836, genres 19, movie_genres 22,050.

## How I handled messy data

- **Release year:** taken from the end of the title, e.g. `Toy Story (1995)`. 13 titles have no year, so those are left empty. I didn't want to guess.
- **Genres:** 34 movies have `(no genres listed)`. I didn't store that as a real genre.
- **Timestamps:** the Unix numbers in `ratings.csv` are converted to proper dates.
- **Missing OMDb values:** stored as NULL. Dates and IMDb ratings are converted to proper types, and anything that can't be converted becomes NULL.
- **Movie not found on OMDb:** the movie is still kept, with `omdb_found = False`, so its ratings and genres still count in the analysis.
- **Network or API error:** the batch script stops, keeps everything it already saved, and can be restarted.
- **Duplicates:** primary keys plus `INSERT IGNORE`, all inside one transaction, so a failed load rolls back cleanly.

## The analysis queries

`queries.sql` answers:

1. Which movie has the highest average rating
2. The top 5 genres by average rating
3. The director with the most movies
4. The average rating for each release year

Two things to keep in mind when reading the results. For Q1, lots of movies have only one or two ratings, so a perfect 5.0 doesn't mean much by itself. It's better to look at the rating count too, or only count movies with at least 10 ratings. For Q3, only movies that OMDb matched have a director, so the answer is based on the movies I've enriched so far, not the whole dataset.

## Choices and assumptions

- I picked MySQL because it's close to what a real team would use, with foreign keys and transactions.
- I kept the OMDb step separate from the load step. Because of the daily limit, I save every API response to a CSV, so I can re-run the load as often as I want without using up any API calls.
- I searched OMDb by title and year, since MovieLens `movies.csv` has no IMDb IDs. They are in `links.csv`, but the assignment only asks for two files.
- I assumed the year in brackets at the end of a title is the release year, and that each user rates a movie only once. The notebook confirms there are no duplicate (user, movie) pairs.

## Problems I ran into

**The API limit.** I couldn't fetch all 9,742 movies in one go. I made the script save each result straight away and skip movies it has already done, so I can run it day after day.

**Titles that don't match.** MovieLens writes titles like `Usual Suspects, The (1995)` or `Seven (a.k.a. Se7en) (1995)`, and OMDb doesn't recognise those. Out of the 990 movies I tried, OMDb found 633 and missed 357. Looking at the misses, around 280 of them are because of this title format and not because the movie is missing from OMDb. Right now I only strip the year and send the rest as it is, so fixing the titles is the first thing I'd improve.

**Missing and inconsistent values.** OMDb returns blanks and odd formats for some fields, so I convert everything to NULL or a proper type before it goes into MySQL.

## Limitations

- Only 990 of the 9,742 movies have been run through OMDb so far, so the director question only covers a small part of the data.
- Box office (like `$229,947,062`) and runtime (like `81 min`) are still stored as text.
- If a movie has two directors, they are stored together as one text value.
- `INSERT IGNORE` stops duplicates, but it won't update a row if the source data changes later.

## What I'd do next

- Clean up the titles before calling the API (move "The" back to the front, remove the alternate-title brackets, retry without the year) and finish enriching all the movies.
- Turn box office and runtime into numbers.
- Add `directors` and `movie_directors` tables, the same way I did for genres, so the director query is exact.
- Switch to `INSERT ... ON DUPLICATE KEY UPDATE` so reruns also update changed rows.
- Add a decade column and rating counts per movie.
- For a real production setup: schedule the job with something like Airflow, call the API with retries and rate limiting, bulk load the ratings, add logging and data-quality checks, and use Docker so setup is the same everywhere.

## Author

Chandini, https://github.com/chandini1605
