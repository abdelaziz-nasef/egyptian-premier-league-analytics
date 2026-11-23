# Egyptian Premier League Analytics (SQL + Excel)

How strong is home advantage in the Egyptian Premier League? Who really owns
the Cairo Derby? This project answers both with 2,031 real match results,
SQL queries, and one Excel dashboard.

![Dashboard preview](docs/dashboard_preview.png)

## What it shows

- **Home advantage by season**: home teams win ~39% of matches vs ~29% for
  away teams. The exception tells a story: in 2012/13, played mostly behind
  closed doors after the Port Said stadium disaster, home advantage almost
  disappeared (36.3% vs 35.6%).
- **The Cairo Derby (Al Ahly vs Zamalek)**: all 10 meetings from 2010-2017.
  Al Ahly dominates: **5 wins, 4 draws, 1 loss, 15-5 on goals**.
- **Top scorer of every season** since 1948/49, from Ahmed Mekkawi to
  Walid Azaro.
- **Most league wins per club**: Al Ahly 151, Zamalek 131, Ismaily 98.

## Data sources (all public)

| Data | Source | Link |
|---|---|---|
| Match results 2010/11-2016/17 (2,031 matches: scores, cards, dates) | Public GitHub dataset `EgyptianLeague.csv` | https://github.com/abdelmalek13/Egyptian-League-Analysis |
| Top scorer per season 1948/49-today | English Wikipedia, "Egyptian Premier League" | https://en.wikipedia.org/wiki/Egyptian_Premier_League |

Note: the 2011/12 and 2012/13 seasons were disrupted after the Port Said
stadium disaster (Feb 2012); the dataset covers the seasons that were played,
labeled by start year (2014 = the 2014/15 season).

## How it's built

```
scripts/fetch_data.py        downloads and cleans both datasets into data/
scripts/analysis.sql         the actual analysis - 5 SQL queries
scripts/build_dashboard.py   loads matches into SQLite, runs analysis.sql,
                             and writes Egyptian_Premier_League_Analytics.xlsx
```

To reproduce:

```bash
python3 scripts/fetch_data.py
python3 scripts/build_dashboard.py
```

The queries are plain standard SQL (GROUP BY, CASE WHEN, UNION ALL,
subqueries) and run unchanged on SQLite; they also work on SQL Server.

## Files

```
Egyptian_Premier_League_Analytics.xlsx   the dashboard (open me first)
data/matches_raw.csv                     original match dataset, unchanged
data/matches_clean.csv                   cleaned matches (season, teams, score, result, cards)
data/top_scorers_by_season.csv           cleaned top scorers table
scripts/analysis.sql                     the SQL behind every number
docs/dashboard_preview.png               screenshot of the dashboard
```

## What I practiced

- SQL: aggregations, conditional sums with CASE WHEN, UNION ALL to reshape
  home/away rows into per-club records, subqueries
- Excel: dashboard layout, KPI cards, clustered column and bar charts
- Cleaning real scraped data: team name variants, seasons cancelled mid-play
- A reproducible pipeline: raw data -> SQL -> workbook, no manual steps
