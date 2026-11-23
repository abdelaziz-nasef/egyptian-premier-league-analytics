#!/usr/bin/env python3
"""Build the 2018/19-2026/27 extension dataset and the combined 2010-2026 dataset.

Sources:
  - data/matches_clean.csv           (2010/11-2017/18, abdelmalek13 GitHub dataset)
  - data/sofascore_raw/NN-NN.json    (2018/19-2026/27, Sofascore public API, tournament 808)

Both sources overlap on 2017/18 and agreed to the score on all cross-checked
matches (e.g. both 2017/18 Cairo derbies), so the extension starts at 2018/19.
Team names are normalized to one canonical spelling per club across both eras.
"""
import csv, json, glob, os, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CANONICAL = {
    # old dataset (2010-2018) spellings
    "El Ahly Cairo": "Al Ahly", "Zamalek SC": "Zamalek", "Ismaily SC": "Ismaily",
    "Harras El Hodoud": "Haras El Hodoud", "Arab Contractors SC": "Arab Contractors (Al Mokawloon)",
    "Wadi Degla FC": "Wadi Degla", "Ghazl Mahalla": "Ghazl El Mahalla",
    "Ittehad Alexandria": "Al Ittihad Alexandria", "Masry Port Said": "Al Masry",
    "Masr El Makasa": "Misr El Makkasa", "Tala'ea El Gaish": "Tala'ea El Gaish",
    "Smouha SC": "Smouha", "Enppi Club": "ENPPI", "El Gouna FC": "El Gouna",
    "Petrojet": "Petrojet", "Aswan FC": "Aswan", "Tanta FC": "Tanta",
    "El Dakhlia SC": "El Dakhleya", "El Minya FC": "El Minya",
    "Telefonat Beni Suef": "Telephonat Beni Suef", "El Nasr": "Al Nasr",
    "El Nasr Tadeen": "El Nasr Tadeen", "El Raja Marsa Matruh": "El Raja",
    "Ala'ab Damanhour": "Ala'ab Damanhour", "Qanah FC": "Canal SC",
    "Entag El Harby": "El Entag El Harby", "El Sharkia Zagazig": "El Sharkia",
    "El Shorta": "El Shorta", "Alassiouty Sport": "Pyramids FC",
    # Sofascore (2018-2026) spellings
    "Al Ahly FC": "Al Ahly", "Pyramids FC": "Pyramids FC", "Ismaily": "Ismaily",
    "National Bank of Egypt": "National Bank of Egypt", "ZED FC": "ZED FC",
    "Cleopatra FC": "Ceramica Cleopatra", "Modern Sport FC": "Modern Sport",
    "Asyut Petroleum": "Asyut Petroleum", "Eastern Company SC": "Eastern Company",
    "Baladiyet El Mahallah": "Baladiyat El Mahalla",
    "Ismailia Electricity Club": "Ismailia Electricity",
    "Suez Petrojet FC": "Petrojet", "Nogoom FC": "Nogoom FC",
    "Pharco FC": "Pharco", "El-Sharkia Enppi FC": "ENPPI",
    "Ghazl El Mahalla FC": "Ghazl El Mahalla", "Tanta": "Tanta",
    "Tala'ea El-Gaish": "Tala'ea El Gaish", "Al-Masry": "Al Masry",
    "Al-Ittihad Alexandria": "Al Ittihad Alexandria",
    "Arab Contractors FC": "Arab Contractors (Al Mokawloon)",
    "Wadi Degla": "Wadi Degla", "El Dakhlya": "El Dakhleya",
    "El-Entag El-Harby": "El Entag El Harby", "Haras El Hodoud": "Haras El Hodoud",
    "Misr El-Makkasa": "Misr El Makkasa", "Aswan SC": "Aswan", "El Raja": "El Raja",
    "Al Nasr Cairo": "Al Nasr", "Abu Qir Fertilizers SC": "Abu Qir Fertilizers",
    "Canal SC": "Canal SC", "Smouha": "Smouha",
}

def canon(name):
    if name not in CANONICAL:
        raise SystemExit(f"unmapped team name: {name!r}")
    return CANONICAL[name]

def result(hg, ag):
    return "Home win" if hg > ag else ("Away win" if ag > hg else "Draw")

def old_season_label(y):  # old labels are start years: 2017 = 2017/18
    return f"{y}/{str(int(y)+1)[2:]}"

# ---- old era ----
old_rows = []
with open(os.path.join(BASE, "data", "matches_clean.csv"), newline="") as f:
    for r in csv.DictReader(f):
        dt = datetime.datetime.strptime(r["date"], "%a, %b %d, %Y").date().isoformat()
        hg, ag = int(r["home_goals"]), int(r["away_goals"])
        old_rows.append({
            "season": old_season_label(r["season"]), "round": r["matchday"], "date": dt,
            "home_team": canon(r["home_team"]), "away_team": canon(r["away_team"]),
            "home_goals": hg, "away_goals": ag, "result": result(hg, ag),
            "source": "abdelmalek13",
        })

# ---- new era (skip 17/18 overlap file; extension starts 18/19) ----
new_rows = []
for path in sorted(glob.glob(os.path.join(BASE, "data", "sofascore_raw", "*.json"))):
    season = "20" + os.path.basename(path)[:2] + "/" + os.path.basename(path)[3:5]
    if season < "2018/19":
        continue  # 17/18 overlap, kept for validation only
    for lab, rnd, ts, home, away, hg, ag in json.load(open(path)):
        new_rows.append({
            "season": season, "round": rnd,
            "date": datetime.datetime.utcfromtimestamp(ts).date().isoformat(),
            "home_team": canon(home), "away_team": canon(away),
            "home_goals": hg, "away_goals": ag, "result": result(hg, ag),
            "source": "sofascore",
        })

old_rows.sort(key=lambda r: r["date"]); new_rows.sort(key=lambda r: r["date"])
all_rows = old_rows + new_rows
FIELDS = ["season", "round", "date", "home_team", "away_team",
          "home_goals", "away_goals", "result", "source"]

def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
        for r in rows: w.writerow(r)

write(os.path.join(BASE, "data", "matches_2018_2026.csv"), new_rows)
write(os.path.join(BASE, "data", "matches_all_2010_2026.csv"), all_rows)
print(f"old era: {len(old_rows)} | new era: {len(new_rows)} | combined: {len(all_rows)}")
per_season = {}
for r in all_rows: per_season[r["season"]] = per_season.get(r["season"], 0) + 1
for s in sorted(per_season): print(f"  {s}: {per_season[s]}")
print("last match:", all_rows[-1]["date"], all_rows[-1]["home_team"],
      all_rows[-1]["home_goals"], "-", all_rows[-1]["away_goals"], all_rows[-1]["away_team"])
