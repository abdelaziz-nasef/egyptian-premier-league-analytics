#!/usr/bin/env python3
"""Run the SQL analysis and build the Excel workbook.

Pipeline: matches_clean.csv -> SQLite -> queries from scripts/analysis.sql
-> result sheets + charts in Egyptian_Premier_League_Analytics.xlsx.

Run after fetch_data.py:  python3 scripts/build_dashboard.py
"""
import csv
import sqlite3
from pathlib import Path

import xlsxwriter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SEASON_LABEL = {str(y): f"{y}/{str(int(y) + 1)[2:]}" for y in range(2010, 2018)}


def run_queries():
    """Load matches into SQLite and run every query in analysis.sql."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    with open(DATA / "matches_clean.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    con.execute("""CREATE TABLE matches(season TEXT, matchday TEXT, date TEXT,
        home_team TEXT, away_team TEXT, home_goals INTEGER, away_goals INTEGER,
        result TEXT, yellow_home INTEGER, yellow_away INTEGER,
        red_home INTEGER, red_away INTEGER)""")
    con.executemany("INSERT INTO matches VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    [tuple(r.values()) for r in rows])
    sql = (ROOT / "scripts" / "analysis.sql").read_text()
    results = []
    for stmt in sql.split(";"):
        # strip leading comment lines from each chunk
        stmt = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")).strip()
        if stmt:
            cur = con.execute(stmt)
            results.append((cur.description and [d[0] for d in cur.description],
                            [list(r) for r in cur.fetchall()]))
    return results


def load_scorers():
    with open(DATA / "top_scorers_by_season.csv", newline="") as f:
        return list(csv.reader(f))


def build_workbook(home_adv, derby, derby_sum, wins, cards, scorers):
    out = ROOT / "Egyptian_Premier_League_Analytics.xlsx"
    wb = xlsxwriter.Workbook(out)
    title = wb.add_format({"bold": True, "font_size": 18, "font_color": "#7A0019"})
    h2 = wb.add_format({"bold": True, "font_size": 12, "font_color": "#7A0019"})
    note = wb.add_format({"font_size": 9, "font_color": "#666666", "text_wrap": True})
    kpi_lbl = wb.add_format({"bold": True, "font_size": 10, "font_color": "#FFFFFF",
                             "bg_color": "#7A0019", "align": "center",
                             "valign": "vcenter", "text_wrap": True})
    kpi_val = wb.add_format({"bold": True, "font_size": 15, "align": "center",
                             "bg_color": "#FBE4E4", "font_color": "#7A0019"})
    hdr = wb.add_format({"bold": True, "bg_color": "#FBE4E4", "border": 1})
    num = wb.add_format({"num_format": "0.0"})

    ws_d = wb.add_worksheet("Dashboard")
    ws_h = wb.add_worksheet("Home Advantage")
    ws_c = wb.add_worksheet("Cairo Derby")
    ws_t = wb.add_worksheet("Top Scorers")
    ws_m = wb.add_worksheet("Matches")

    # ---- Home Advantage sheet ----
    ws_h.write_row(0, 0, home_adv[0], hdr)
    for i, r in enumerate(home_adv[1], start=1):
        for j, v in enumerate(r):
            ws_h.write(i, j, v)
    nh = len(home_adv[1])

    # ---- Cairo Derby sheet ----
    ws_c.write(0, 0, "Head-to-head summary", h2)
    ws_c.write_row(1, 0, derby_sum[0], hdr)
    for i, r in enumerate(derby_sum[1], start=2):
        for j, v in enumerate(r):
            ws_c.write(i, j, v)
    ws_c.write(5, 0, "Every derby in the dataset", h2)
    ws_c.write_row(6, 0, derby[0], hdr)
    for i, r in enumerate(derby[1], start=7):
        for j, v in enumerate(r):
            ws_c.write(i, j, v)
    ws_c.set_column(0, 6, 14)

    # ---- Top Scorers sheet ----
    ws_t.write_row(0, 0, scorers[0], hdr)
    for i, r in enumerate(scorers[1:], start=1):
        for j, v in enumerate(r):
            ws_t.write(i, j, int(v) if j == 3 and v.isdigit() else v)
    ns = len(scorers) - 1
    ws_t.set_column(0, 2, 24)

    # ---- Matches sheet ----
    ws_m.write_row(0, 0, ["season", "matchday", "date", "home_team", "away_team",
                          "home_goals", "away_goals", "result"], hdr)
    with open(DATA / "matches_clean.csv", newline="") as f:
        for i, r in enumerate(csv.DictReader(f), start=1):
            ws_m.write_row(i, 0, [r["season"], r["matchday"], r["date"],
                                  r["home_team"], r["away_team"],
                                  int(r["home_goals"]), int(r["away_goals"]), r["result"]])

    # ---- Dashboard ----
    ws_d.hide_gridlines(2)
    ws_d.set_column("A:A", 2)
    ws_d.set_column("B:J", 13)
    ws_d.set_landscape()
    ws_d.fit_to_pages(1, 1)
    ws_d.write("B2", "Egyptian Premier League Analytics", title)
    ws_d.write("B3", "2,031 matches, seasons 2010/11-2016/17 - home advantage, the Cairo Derby, top scorers", note)

    ahly = next(r for r in derby_sum[1] if r[0] == "Al Ahly")
    zam = next(r for r in derby_sum[1] if r[0] == "Zamalek")
    home_pct = round(sum(r[5] * r[1] for r in home_adv[1]) / sum(r[1] for r in home_adv[1]), 1)
    scorer_1617 = next(r for r in reversed(scorers[1:]) if r[0].startswith("2016"))
    kpis = [
        (f"Cairo Derby ({ahly[1]} meetings)", f"Al Ahly {ahly[2]}-{zam[2]} Zamalek ({ahly[3]} draws)"),
        ("Home win rate, all seasons", f"{home_pct}%"),
        (f"Top scorer {scorer_1617[0]}", f"{scorer_1617[1]}, {scorer_1617[3]} goals"),
    ]
    for k, (lbl, val) in enumerate(kpis):
        col = 1 + k * 3
        ws_d.merge_range(4, col, 4, col + 2, lbl, kpi_lbl)
        ws_d.merge_range(5, col, 5, col + 2, val, kpi_val)

    # Chart 1: home vs away win % by season
    ch1 = wb.add_chart({"type": "column"})
    ch1.add_series({"name": "Home win %",
                    "categories": ["Home Advantage", 1, 0, nh, 0],
                    "values": ["Home Advantage", 1, 5, nh, 5],
                    "fill": {"color": "#7A0019"}})
    ch1.add_series({"name": "Away win %",
                    "categories": ["Home Advantage", 1, 0, nh, 0],
                    "values": ["Home Advantage", 1, 6, nh, 6],
                    "fill": {"color": "#999999"}})
    ch1.set_title({"name": "Home advantage by season (% of matches won)"})
    ch1.set_x_axis({"name": "Season (start year)"})
    ch1.set_legend({"position": "bottom"})
    ch1.set_size({"width": 860, "height": 380})
    ws_d.insert_chart("B8", ch1)

    # Chart 2: most wins per club
    ws_w = wb.add_worksheet("Club Wins")
    ws_w.write_row(0, 0, wins[0], hdr)
    for i, r in enumerate(wins[1], start=1):
        for j, v in enumerate(r):
            ws_w.write(i, j, v)
    nw = len(wins[1])
    ch2 = wb.add_chart({"type": "bar"})
    ch2.add_series({"name": "Total wins 2010-2017",
                    "categories": ["Club Wins", 1, 0, nw, 0],
                    "values": ["Club Wins", 1, 1, nw, 1],
                    "fill": {"color": "#7A0019"}})
    ch2.set_title({"name": "Most league wins per club (2010-2017)"})
    ch2.set_legend({"none": True})
    ch2.set_size({"width": 860, "height": 380})
    ws_d.insert_chart("B29", ch2)

    ws_d.write("B50", "Data: match results via the public GitHub dataset "
                      "abdelmalek13/Egyptian-League-Analysis (EgyptianLeague.csv); "
                      "top scorers by season from the English Wikipedia article "
                      "'Egyptian Premier League'. Analysis queries in scripts/analysis.sql.", note)

    wb.close()
    print(f"Workbook written: {out}")


def main():
    (home_adv, derby, derby_sum, wins, cards) = run_queries()
    scorers = load_scorers()
    build_workbook(home_adv, derby, derby_sum, wins, cards, scorers)

    print("\nHome advantage by season (home win % / away win %):")
    for r in home_adv[1]:
        print(f"  {r[0]}: {r[5]}% / {r[6]}%  ({r[1]} matches)")
    print("\nCairo Derby summary:")
    for r in derby_sum[1]:
        print(f"  {r[0]}: {r[2]}W {r[3]}D {r[4]}L, goals {r[5]}-{r[6]}")
    print("\nTop 5 clubs by wins:", [(r[0], r[1]) for r in wins[1][:5]])


if __name__ == "__main__":
    main()
