# Egyptian Premier League Analytics

**3,373 match records | 2015/16-2026/27 | SQL + Excel**

An analysis of home advantage, the Cairo Derby, Al Ahly vs Pyramids,
club wins, scoring trends and calculated current-season standings.
The workbook is a static snapshot of results through **31 October 2026**,
not a live feed. The older 2010-start version remains in Git history only.

![Excel dashboard, rendered from the workbook](docs/dashboard_preview.png)

## Open the project

Download `Egyptian_Premier_League_Analytics.xlsx` and start on **Dashboard**.
Four KPI cards sit above three editable Excel charts and a leading-teams
preview. Links take you to filterable detail tables. All 3,373 match rows
are included in **Match Data**. **Read Me** explains sources and limits.

## Findings in this snapshot

- Home sides win **36.1%** of recorded matches; away sides **30.9%**.
  The gap is **5.2 percentage points**, not 5.2 percent.
- Cairo Derby, selected range: **23 records**, Al Ahly **14 wins**,
  **5 draws**, Zamalek **4 wins**. Recorded goals: **42-20** to Al Ahly.
  These are recorded results and can include awarded scores, not only games played.
- Since 2018/19, Ahly vs Pyramids: **16 records**, Ahly **5 wins**,
  **5 draws**, Pyramids **6 wins**. Pre-2018 predecessor records remain in
  the full detail tab but are excluded from this modern-rivalry KPI.
- League wins in the selected records: **Al Ahly 260**, **Zamalek 217**,
  **Pyramids 169**, **Al Masry 146**. Wins are not league titles.
- The calculated 2026/27 table has Pyramids on **24 points from 8 games**,
  Al Ahly **20**, Zamalek **19**. This is a calculation from results,
  not a reproduction of an official table or its deductions/tie-breaks.

## Sources and coverage

| Source | Used for | Link |
|---|---|---|
| Public `EgyptianLeague.csv` dataset | 918 records, 2015/16-2017/18 | https://github.com/abdelmalek13/Egyptian-League-Analysis |
| Sofascore public API, tournament 808 | 2,455 records, 2018/19-2026/27 | https://www.sofascore.com/tournament/football/egypt/premier-league/808 |
| Wikipedia season top-scorer table | Completed-season awards from 2015/16 | https://en.wikipedia.org/wiki/Egyptian_Premier_League |

The 2017/18 API snapshot is kept as an overlap check, not merged twice.
Club names are normalized so that spelling changes do not split one club
into several groups. Alassiouty Sport is grouped under Pyramids FC.

**Limits:** 2019/20 has 298 source records, not a usual 306. Other season
counts also differ, and this project does not guarantee complete season
coverage. Formats changed, and 2026/27 is in progress. Source scores may
include awarded outcomes. The home/away field does not establish the
actual venue or crowd effect. No causal explanation is inferred from it.
The scorer table is a separate season-award source, not player-level
statistics derived from the match CSV. No 2026/27 scorer award is claimed.

## How the pieces connect

```text
Public match CSV + Sofascore season JSON + Wikipedia scorer table
                    |
             fetch / clean (Python)
                    |
       normalize club names, filter range, merge
                    |
          data/matches_2015_2026.csv
                    |
          SQLite + scripts/analysis.sql
                    |
          result tables + Excel charts
                    |
      Egyptian_Premier_League_Analytics.xlsx
                    |
       GitHub stores the code, data and workbook
```

**Python** moves and cleans the data and builds the file. **SQL** answers
the questions. **SQLite** runs that SQL in a small temporary database.
**Excel** displays the resulting tables and charts. **Git/GitHub** stores
versions and lets someone inspect or download the work. There is no
Power BI file, live Excel data connection, web app or machine-learning model.

## Files and scripts

| File | Purpose |
|---|---|
| `scripts/fetch_data.py` | Downloads the older source CSV and Wikipedia table; keeps only the selected seasons and cleans their columns. |
| `scripts/fetch_recent.py` | Requests season/round results from Sofascore and writes JSON snapshots. Access can be rate-limited; checked-in snapshots support offline rebuilding. |
| `scripts/build_recent_dataset.py` | Converts dates, normalizes team names, skips the 2017/18 overlap, merges the sources and rejects duplicate fixture keys. |
| `scripts/analysis.sql` | Seven SQLite result sets: home advantage, derby fixtures, derby totals, Pyramids fixtures, club wins, season goals and calculated current table. |
| `scripts/analysis_recent.sql` | Compatibility copy of the same current-range queries. |
| `scripts/build_dashboard.py` | Loads the merged CSV into in-memory SQLite, runs the SQL and uses XlsxWriter to create formatted detail tables, navigation and editable charts. |
| `data/matches_raw.csv` | Source-shaped match rows for 2015/16-2017/18. |
| `data/matches_clean.csv` | Cleaned older-source rows in the selected range. |
| `data/sofascore_raw/*.json` | Saved season snapshots, including 2017/18 for overlap checking. |
| `data/matches_2018_2026.csv` | Cleaned Sofascore extension. |
| `data/matches_2015_2026.csv` | The merged analysis input, 3,373 records. |
| `data/top_scorers_by_season.csv` | Selected completed-season scorer awards. |
| `docs/findings.json` | Machine-readable summary calculated during workbook creation. |
| `docs/dashboard_preview.png` | Actual render of the workbook's Dashboard sheet. |
| `docs/dashboard.pdf` | One-page PDF export of that dashboard. |
| `requirements.txt` | Excel-writing dependency; other build modules are Python standard library. |

The SQL uses SQLite expressions such as `SUM(result = 'Home win')` and
`LIMIT`. For SQL Server, replace these with `CASE` expressions and `TOP`.

## Rebuild

```bash
pip install -r requirements.txt
# Offline rebuild using the checked-in source snapshots:
python scripts/build_recent_dataset.py
python scripts/build_dashboard.py

# Optional source refresh before rebuilding:
python scripts/fetch_data.py
python scripts/fetch_recent.py
```

The API snapshot is dated. A failed or partial refresh should be investigated
before replacing it. The current fetch script has fixed season IDs and a
round-based endpoint; new seasons and playoff structures may need changes.
The workbook itself does not refresh when opened. The dashboard preview is
exported separately from the finished workbook, not generated by the builder.
