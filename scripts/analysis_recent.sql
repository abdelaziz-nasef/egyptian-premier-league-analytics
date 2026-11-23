-- Egyptian Premier League analytics, extension queries (2015/16-2026/27).
-- Input: data/matches_2015_2026.csv (build_recent_dataset.py output).

-- Q1. Home advantage by season, 12 seasons
SELECT season,
       COUNT(*) AS matches,
       SUM(result = 'Home win') AS home_wins,
       SUM(result = 'Draw') AS draws,
       SUM(result = 'Away win') AS away_wins,
       ROUND(100.0 * SUM(result = 'Home win') / COUNT(*), 1) AS home_win_pct,
       ROUND(100.0 * SUM(result = 'Away win') / COUNT(*), 1) AS away_win_pct
FROM matches GROUP BY season ORDER BY season;

-- Q2. Cairo derby in the selected range (Al Ahly vs Zamalek)
SELECT season, date, home_team, home_goals, away_goals, away_team
FROM matches
WHERE (home_team = 'Al Ahly' AND away_team = 'Zamalek')
   OR (home_team = 'Zamalek' AND away_team = 'Al Ahly')
ORDER BY date;

SELECT
  SUM(CASE WHEN (home_team='Al Ahly' AND home_goals>away_goals)
            OR (away_team='Al Ahly' AND away_goals>home_goals) THEN 1 ELSE 0 END) AS ahly_wins,
  SUM(home_goals = away_goals) AS draws,
  SUM(CASE WHEN (home_team='Zamalek' AND home_goals>away_goals)
            OR (away_team='Zamalek' AND away_goals>home_goals) THEN 1 ELSE 0 END) AS zamalek_wins,
  SUM(CASE WHEN home_team='Al Ahly' THEN home_goals ELSE away_goals END) AS ahly_goals,
  SUM(CASE WHEN home_team='Zamalek' THEN home_goals ELSE away_goals END) AS zamalek_goals
FROM matches
WHERE (home_team = 'Al Ahly' AND away_team = 'Zamalek')
   OR (home_team = 'Zamalek' AND away_team = 'Al Ahly');

-- Q3. Al Ahly vs Pyramids head-to-head (selected range, predecessor names normalized)
SELECT season, date, home_team, home_goals, away_goals, away_team
FROM matches
WHERE (home_team = 'Al Ahly' AND away_team = 'Pyramids FC')
   OR (home_team = 'Pyramids FC' AND away_team = 'Al Ahly')
ORDER BY date;

-- Q4. Most wins, in the selected range (2015/16-2026/27)
SELECT team, SUM(wins) AS wins FROM (
  SELECT home_team AS team, SUM(result = 'Home win') AS wins FROM matches GROUP BY home_team
  UNION ALL
  SELECT away_team AS team, SUM(result = 'Away win') AS wins FROM matches GROUP BY away_team
) GROUP BY team ORDER BY wins DESC LIMIT 10;

-- Q5. Goals per season
SELECT season, SUM(home_goals + away_goals) AS goals,
       ROUND(1.0 * SUM(home_goals + away_goals) / COUNT(*), 2) AS goals_per_game
FROM matches GROUP BY season ORDER BY season;

-- Q6. 2026/27 league table after Round 8 (current season in progress)
WITH results AS (
  SELECT home_team AS team,
         CASE WHEN home_goals > away_goals THEN 3 WHEN home_goals = away_goals THEN 1 ELSE 0 END AS pts,
         home_goals AS gf, away_goals AS ga,
         CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END AS w,
         CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END AS d,
         CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END AS l
  FROM matches WHERE season = '2026/27'
  UNION ALL
  SELECT away_team,
         CASE WHEN away_goals > home_goals THEN 3 WHEN away_goals = home_goals THEN 1 ELSE 0 END,
         away_goals, home_goals,
         CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END,
         CASE WHEN away_goals = home_goals THEN 1 ELSE 0 END,
         CASE WHEN away_goals < home_goals THEN 1 ELSE 0 END
  FROM matches WHERE season = '2026/27'
)
SELECT team, COUNT(*) AS played, SUM(w) AS won, SUM(d) AS drawn, SUM(l) AS lost,
       SUM(gf) AS gf, SUM(ga) AS ga, SUM(gf) - SUM(ga) AS gd, SUM(pts) AS points
FROM results GROUP BY team
ORDER BY points DESC, gd DESC, gf DESC;
