#!/usr/bin/env python3
"""Fetch and clean the datasets for the Egyptian Premier League analysis.

Sources:
1. Match results 2010-2017: EgyptianLeague.csv from the public GitHub repo
   abdelmalek13/Egyptian-League-Analysis (2,031 matches with scores and cards).
2. Top scorer per season 1948-today: the "Top scorers by season" table on the
   English Wikipedia page for the Egyptian Premier League.

Run:  python3 scripts/fetch_data.py
"""
import csv
import re
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)

MATCHES_URL = (
    "https://raw.githubusercontent.com/abdelmalek13/Egyptian-League-Analysis/"
    "master/EgyptianLeague.csv"
)
WIKI_URL = "https://en.wikipedia.org/wiki/Egyptian_Premier_League"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def clean_matches() -> None:
    raw = fetch(MATCHES_URL)
    (DATA / "matches_raw.csv").write_bytes(raw)
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    with open(DATA / "matches_clean.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["season", "matchday", "date", "home_team", "away_team",
                    "home_goals", "away_goals", "result",
                    "yellow_home", "yellow_away", "red_home", "red_away"])
        for r in rows:
            hg, ag = int(r["Home Goals"]), int(r["Away Goals"])
            result = "Home win" if hg > ag else "Away win" if ag > hg else "Draw"
            w.writerow([r["Season"], r["MatchDay"], r["Date"], r["Home Team"],
                        r["Away Team"], hg, ag, result,
                        r["Yellow Home"] or 0, r["Yellow Away"] or 0,
                        (r["Red Home"] or 0), (r["Red Away"] or 0)])
    print(f"matches_clean.csv: {len(rows)} matches")


def clean_scorers() -> None:
    html = fetch(WIKI_URL).decode("utf-8", errors="replace")
    tables = re.findall(r"<table[^>]*>.*?</table>", html, re.S)
    target = None
    for t in tables:
        head = re.sub("<[^>]+>", " ", t[:400])
        if re.search(r"Season\s+Player\s+Club\s+Goals", head):
            target = t
            break
    if target is None:
        raise SystemExit("top scorers table not found on Wikipedia page")
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", target, re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
        cells = [re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", c)).strip() for c in cells]
        # some rows carry a second winner without repeating the season
        if len(cells) == 4 and re.match(r"^\d{4}", cells[0]):
            out.append(cells)
        elif len(cells) == 3 and out:  # shared award, same season
            out.append([out[-1][0], *cells])
    with open(DATA / "top_scorers_by_season.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["season", "player", "club", "goals"])
        w.writerows(out[1:])  # drop header row from the page table
    print(f"top_scorers_by_season.csv: {len(out) - 1} season winners")


if __name__ == "__main__":
    clean_matches()
    clean_scorers()
