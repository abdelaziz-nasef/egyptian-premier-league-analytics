#!/usr/bin/env python3
"""Run the SQL analysis and build the Excel workbook.

Pipeline: matches_all_2010_2026.csv -> SQLite -> queries from analysis_recent.sql
-> result sheets + charts in Egyptian_Premier_League_Analytics.xlsx.

Run after build_recent_dataset.py:  python3 scripts/build_dashboard.py
"""
import csv
import sqlite3
from pathlib import Path

import xlsxwriter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

MAROON = "#7A0019"


def run_queries():
    """Load the combined dataset into SQLite and run analysis_recent.sql in order."""
    con = sqlite3.connect(":memory:")
    with open(DATA / "matches_all_2010_2026.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    con.execute("""CREATE TABLE matches(season TEXT, round TEXT, date TEXT,
        home_team TEXT, away_team TEXT, home_goals INTEGER, away_goals INTEGER,
        result TEXT, source TEXT)""")
    con.executemany("INSERT INTO matches VALUES(?,?,?,?,?,?,?,?,?)",
                    [tuple(r.values()) for r in rows])
    sql = (ROOT / "scripts" / "analysis_recent.sql").read_text()
    out = []
    for stmt in sql.split(";"):
        stmt = "\n".join(l for l in stmt.splitlines()
                         if not l.strip().startswith("--")).strip()
        if stmt:
            cur = con.execute(stmt)
            out.append(([d[0] for d in cur.description], [list(r) for r in cur.fetchall()]))
    return out


def write_table(ws, row0, col0, header, rows, hdr_fmt):
    ws.write_row(row0, col0, header, hdr_fmt)
    for i, r in enumerate(rows, start=row0 + 1):
        for j, v in enumerate(r):
            ws.write(i, j, v)
    return row0 + len(rows)


def main():
    (home_adv, derby_list, derby_sum, pyr_list,
     wins, goals, table26) = run_queries()

    with open(DATA / "top_scorers_by_season.csv", newline="") as f:
        scorers = list(csv.reader(f))

    # Pyramids modern-era aggregate (2018/19 onward) computed from the H2H list
    pyr_modern = [r for r in pyr_list[1] if r[0] >= "2018/19"]
    a_w = sum(1 for r in pyr_modern
              if (r[2] == "Al Ahly" and r[3] > r[4]) or (r[5] == "Al Ahly" and r[4] > r[3]))
    p_w = sum(1 for r in pyr_modern
              if (r[2] == "Pyramids FC" and r[3] > r[4]) or (r[5] == "Pyramids FC" and r[4] > r[3]))
    draws = len(pyr_modern) - a_w - p_w

    total_matches = sum(r[1] for r in home_adv[1])
    home_pct = round(sum(r[5] * r[1] for r in home_adv[1]) / total_matches, 1)
    away_pct = round(sum(r[6] * r[1] for r in home_adv[1]) / total_matches, 1)
    ahly_w, d_d, zam_w = derby_sum[1][0][0], derby_sum[1][0][1], derby_sum[1][0][2]
    n_derby = ahly_w + d_d + zam_w
    top = table26[1][0]   # league leaders after Round 8
    scorer_2526 = scorers[-2] if scorers[-1][0].startswith("2026") else scorers[-1]

    out = ROOT / "Egyptian_Premier_League_Analytics.xlsx"
    wb = xlsxwriter.Workbook(out)
    title = wb.add_format({"bold": True, "font_size": 18, "font_color": MAROON})
    h2 = wb.add_format({"bold": True, "font_size": 12, "font_color": MAROON})
    note = wb.add_format({"font_size": 9, "font_color": "#666666", "text_wrap": True})
    kpi_lbl = wb.add_format({"bold": True, "font_size": 10, "font_color": "#FFFFFF",
                             "bg_color": MAROON, "align": "center",
                             "valign": "vcenter", "text_wrap": True})
    kpi_val = wb.add_format({"bold": True, "font_size": 14, "align": "center",
                             "valign": "vcenter", "bg_color": "#FBE4E4",
                             "font_color": MAROON, "text_wrap": True})
    hdr = wb.add_format({"bold": True, "bg_color": "#FBE4E4", "border": 1})

    ws_d = wb.add_worksheet("Dashboard")
    ws_h = wb.add_worksheet("Home Advantage")
    ws_c = wb.add_worksheet("Cairo Derby")
    ws_p = wb.add_worksheet("Ahly vs Pyramids")
    ws_t26 = wb.add_worksheet("Table 2026-27")
    ws_g = wb.add_worksheet("Goals by Season")
    ws_w = wb.add_worksheet("Club Wins All-Time")
    ws_s = wb.add_worksheet("Top Scorers")
    ws_m1 = wb.add_worksheet("Matches 2010-2018")
    ws_m2 = wb.add_worksheet("Matches 2018-2026")

    # ---- Home Advantage sheet (17 seasons) ----
    nh = write_table(ws_h, 0, 0, home_adv[0], home_adv[1], hdr)
    ws_h.set_column(0, 6, 12)

    # ---- Cairo Derby sheet ----
    ws_c.write(0, 0, "All-time head-to-head (2010/11-2026/27)", h2)
    ws_c.write_row(1, 0, ["Al Ahly wins", "Draws", "Zamalek wins",
                          "Al Ahly goals", "Zamalek goals"], hdr)
    ws_c.write_row(2, 0, derby_sum[1][0])
    ws_c.write(4, 0, f"Every Cairo Derby in the dataset ({n_derby} meetings)", h2)
    write_table(ws_c, 5, 0, derby_list[0], derby_list[1], hdr)
    ws_c.set_column(0, 6, 14)

    # ---- Ahly vs Pyramids sheet ----
    ws_p.write(0, 0, "Head-to-head since Pyramids' rise (2018/19 onward)", h2)
    ws_p.write_row(1, 0, ["Meetings", "Al Ahly wins", "Draws", "Pyramids wins"], hdr)
    ws_p.write_row(2, 0, [len(pyr_modern), a_w, draws, p_w])
    ws_p.write(3, 0, "Pyramids won both 2025/26 meetings (2-0 in Cairo, 3-0 at home). "
                     "Next meeting: Nov 23, 2026 (Round 9 of 2026/27) - not yet played "
                     "when this dataset was built.", note)
    ws_p.write(5, 0, "Every meeting in the dataset (Pyramids appear as Alassiouty "
                     "Sport before their 2018 rename)", h2)
    write_table(ws_p, 6, 0, pyr_list[0], pyr_list[1], hdr)
    ws_p.set_column(0, 6, 14)

    # ---- 2026/27 table sheet ----
    ws_t26.write(0, 0, "League table after Round 8 (as of Oct 31, 2026 - season in progress)", h2)
    write_table(ws_t26, 1, 0, table26[0], table26[1], hdr)
    ws_t26.set_column(0, 0, 26)
    ws_t26.set_column(1, 8, 8)

    # ---- Goals sheet ----
    write_table(ws_g, 0, 0, goals[0], goals[1], hdr)
    ws_g.set_column(0, 2, 14)

    # ---- Club wins sheet ----
    nw = write_table(ws_w, 0, 0, wins[0], wins[1], hdr)
    ws_w.set_column(0, 0, 26)

    # ---- Top scorers sheet ----
    ws_s.write_row(0, 0, scorers[0], hdr)
    for i, r in enumerate(scorers[1:], start=1):
        for j, v in enumerate(r):
            ws_s.write(i, j, int(v) if j == 3 and v.isdigit() else v)
    ws_s.set_column(0, 2, 24)

    # ---- Match data sheets ----
    cols = ["season", "round", "date", "home_team", "away_team",
            "home_goals", "away_goals", "result"]
    for ws, fname in ((ws_m1, "matches_all_2010_2026.csv"), (ws_m2, "matches_2018_2026.csv")):
        ws.write_row(0, 0, cols, hdr)
        with open(DATA / fname, newline="") as f:
            rows = list(csv.DictReader(f))
        if ws is ws_m1:
            rows = [r for r in rows if r["season"] < "2018/19"]
        for i, r in enumerate(rows, start=1):
            ws.write_row(i, 0, [r["season"], r["round"], r["date"], r["home_team"],
                                r["away_team"], int(r["home_goals"]),
                                int(r["away_goals"]), r["result"]])
        ws.set_column(3, 4, 24)

    # ---- Dashboard ----
    ws_d.hide_gridlines(2)
    ws_d.set_column("A:A", 2)
    ws_d.set_column("B:M", 11)
    ws_d.set_landscape()
    ws_d.fit_to_pages(1, 1)
    ws_d.write("B2", "Egyptian Premier League Analytics", title)
    ws_d.set_row(2, 28)
    ws_d.write("B3", f"{total_matches:,} matches, 17 seasons 2010/11-2026/27, "
                     "results through Oct 31, 2026", note)

    kpis = [
        (f"Cairo Derby all-time ({n_derby} meetings)",
         f"Al Ahly {ahly_w}-{d_d}-{zam_w} Zamalek"),
        ("Al Ahly vs Pyramids since 2018",
         f"{a_w}W-{draws}D-{p_w}L - Pyramids won both 25/26 meetings"),
        ("2026/27 after Round 8",
         f"{top[0]} perfect: {top[8]} pts in {top[1]} games, Al Ahly 2nd on 20"),
        ("Home win rate, 2010-2026",
         f"{home_pct}% home vs {away_pct}% away"),
    ]
    for k, (lbl, val) in enumerate(kpis):
        col = 1 + k * 3
        ws_d.merge_range(4, col, 4, col + 2, lbl, kpi_lbl)
        ws_d.merge_range(5, col, 5, col + 2, val, kpi_val)
    ws_d.set_row(5, 34)

    ch1 = wb.add_chart({"type": "column"})
    ch1.add_series({"name": "Home win %",
                    "categories": ["Home Advantage", 1, 0, nh, 0],
                    "values": ["Home Advantage", 1, 5, nh, 5],
                    "fill": {"color": MAROON}})
    ch1.add_series({"name": "Away win %",
                    "categories": ["Home Advantage", 1, 0, nh, 0],
                    "values": ["Home Advantage", 1, 6, nh, 6],
                    "fill": {"color": "#999999"}})
    ch1.set_title({"name": "Home advantage by season, 2010/11-2026/27"})
    ch1.set_x_axis({"name": "Season"})
    ch1.set_legend({"position": "bottom"})
    ch1.set_size({"width": 1100, "height": 360})
    ws_d.insert_chart("B8", ch1)

    ch2 = wb.add_chart({"type": "bar"})
    ch2.add_series({"name": "League wins 2010-2026",
                    "categories": ["Club Wins All-Time", 1, 0, nw, 0],
                    "values": ["Club Wins All-Time", 1, 1, nw, 1],
                    "fill": {"color": MAROON}})
    ch2.set_title({"name": "Most league wins per club, 2010/11-2026/27"})
    ch2.set_legend({"none": True})
    ch2.set_y_axis({"reverse": True})
    ch2.set_size({"width": 1100, "height": 430})
    ws_d.insert_chart("B27", ch2)

    ws_d.set_row(50, 42)
    ws_d.write("B50", "Sources: 2010/11-2017/18 via the public GitHub dataset "
                      "abdelmalek13/Egyptian-League-Analysis; 2018/19-2026/27 via the "
                      "Sofascore public API (tournament 808), cross-validated on the "
                      "overlapping 2017/18 season; top scorers from Wikipedia. "
                      "Analysis queries in scripts/analysis_recent.sql.", note)
    ws_d.write("B55", " ", note)  # extend print range past chart 2
    wb.close()
    print(f"Workbook written: {out}")
    print(f"KPIs: derby {ahly_w}-{d_d}-{zam_w} | Ahly-Pyramids {a_w}W-{draws}D-{p_w}L | "
          f"leader {top[0]} {top[8]}pts | home {home_pct}% vs away {away_pct}%")


if __name__ == "__main__":
    main()
