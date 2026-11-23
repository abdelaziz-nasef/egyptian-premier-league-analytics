#!/usr/bin/env python3
"""Fetch Egyptian Premier League results 2018/19-today from Sofascore's public API.

Sofascore (tournament id 808) carries full match-level results for every season
from 2018/19 onward. One request per round per season:

    GET https://www.sofascore.com/api/v1/unique-tournament/808/season/{sid}/events/round/{r}

Season ids used for this dataset (new seasons get new ids - look them up under
the tournament page's API if extending):
    2018/19=18033  2019/20=25455  2020/21=34930  2021/22=39373  2022/23=46713
    2023/24=55005  2024/25=68147  2025/26=79317  2026/27=100148

Writes one JSON file per season to data/sofascore_raw/ in the row format
[season, round, unix_ts, home, away, home_goals, away_goals].
Note: Sofascore rate-limits plain scripts (Cloudflare); if requests fails,
run the same endpoints in a browser console on sofascore.com and save the JSON.
"""
import json, os, time, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEASONS = {"18-19": 18033, "19-20": 25455, "20-21": 34930, "21-22": 39373,
           "22-23": 46713, "23-24": 55005, "24-25": 68147, "25-26": 79317,
           "26-27": 100148}
URL = "https://www.sofascore.com/api/v1/unique-tournament/808/season/{sid}/events/round/{r}"

def fetch(label, sid):
    rows = []
    rnd = 1
    while rnd <= 45:
        with urllib.request.urlopen(URL.format(sid=sid, r=rnd)) as resp:
            events = json.load(resp).get("events", [])
        finished = [e for e in events if e["status"]["type"] == "finished"]
        for e in finished:
            rows.append([label, rnd, e["startTimestamp"], e["homeTeam"]["name"],
                         e["awayTeam"]["name"], e["homeScore"]["current"],
                         e["awayScore"]["current"]])
        if not events:  # playoff/short formats leave gaps; stop past the listed rounds
            break
        rnd += 1
        time.sleep(0.5)
    out = os.path.join(BASE, "data", "sofascore_raw", f"{label}.json")
    json.dump(rows, open(out, "w"))
    print(label, len(rows), "finished matches")

if __name__ == "__main__":
    os.makedirs(os.path.join(BASE, "data", "sofascore_raw"), exist_ok=True)
    for label, sid in SEASONS.items():
        fetch(label, sid)
