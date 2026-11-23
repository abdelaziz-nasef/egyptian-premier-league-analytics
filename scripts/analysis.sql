-- Egyptian Premier League analysis queries
-- Dialect: standard SQL, runs on SQLite (and SQL Server with no changes except
-- ROUND is fine in both). Table: matches(season, matchday, date, home_team,
-- away_team, home_goals, away_goals, result, yellow_home, yellow_away,
-- red_home, red_away)

-- 1. Home advantage per season: win rates and average goals
SELECT season,
       COUNT(*) AS matches,
       SUM(CASE WHEN result = 'Home win' THEN 1 ELSE 0 END) AS home_wins,
       SUM(CASE WHEN result = 'Draw' THEN 1 ELSE 0 END) AS draws,
       SUM(CASE WHEN result = 'Away win' THEN 1 ELSE 0 END) AS away_wins,
       ROUND(100.0 * SUM(CASE WHEN result = 'Home win' THEN 1 ELSE 0 END) / COUNT(*), 1) AS home_win_pct,
       ROUND(100.0 * SUM(CASE WHEN result = 'Away win' THEN 1 ELSE 0 END) / COUNT(*), 1) AS away_win_pct,
       ROUND(AVG(home_goals), 2) AS avg_home_goals,
       ROUND(AVG(away_goals), 2) AS avg_away_goals
FROM matches
GROUP BY season
ORDER BY season;

-- 2. Cairo Derby: Al Ahly vs Zamalek head-to-head, every meeting
SELECT season, date, home_team, home_goals, away_goals, away_team, result
FROM matches
WHERE (home_team = 'El Ahly Cairo' AND away_team = 'Zamalek SC')
   OR (home_team = 'Zamalek SC' AND away_team = 'El Ahly Cairo')
ORDER BY season, date;

-- 3. Cairo Derby summary: wins per side and goals (each club as home and away)
SELECT club,
       COUNT(*) AS derbies,
       SUM(win) AS wins,
       SUM(draw) AS draws,
       SUM(loss) AS losses,
       SUM(goals_for) AS goals_for,
       SUM(goals_against) AS goals_against
FROM (
    SELECT 'Al Ahly' AS club,
           CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END AS win,
           CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END AS draw,
           CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END AS loss,
           home_goals AS goals_for, away_goals AS goals_against
    FROM matches WHERE home_team = 'El Ahly Cairo' AND away_team = 'Zamalek SC'
    UNION ALL
    SELECT 'Al Ahly',
           CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END,
           CASE WHEN away_goals = home_goals THEN 1 ELSE 0 END,
           CASE WHEN away_goals < home_goals THEN 1 ELSE 0 END,
           away_goals, home_goals
    FROM matches WHERE away_team = 'El Ahly Cairo' AND home_team = 'Zamalek SC'
    UNION ALL
    SELECT 'Zamalek',
           CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END,
           CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END,
           CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END,
           home_goals, away_goals
    FROM matches WHERE home_team = 'Zamalek SC' AND away_team = 'El Ahly Cairo'
    UNION ALL
    SELECT 'Zamalek',
           CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END,
           CASE WHEN away_goals = home_goals THEN 1 ELSE 0 END,
           CASE WHEN away_goals < home_goals THEN 1 ELSE 0 END,
           away_goals, home_goals
    FROM matches WHERE away_team = 'Zamalek SC' AND home_team = 'El Ahly Cairo'
) AS derby
GROUP BY club;

-- 4. Most league wins per club across all seasons (league titles proxy)
SELECT club, SUM(wins) AS total_wins, COUNT(*) AS matches,
       ROUND(100.0 * SUM(wins) / COUNT(*), 1) AS win_pct
FROM (
    SELECT home_team AS club,
           CASE WHEN result = 'Home win' THEN 1 ELSE 0 END AS wins
    FROM matches
    UNION ALL
    SELECT away_team,
           CASE WHEN result = 'Away win' THEN 1 ELSE 0 END
    FROM matches
) AS all_games
GROUP BY club
ORDER BY total_wins DESC
LIMIT 10;

-- 5. Most cards per club (fair play / aggression ranking)
SELECT club, SUM(cards) AS total_cards
FROM (
    SELECT home_team AS club, yellow_home + red_home AS cards FROM matches
    UNION ALL
    SELECT away_team, yellow_away + red_away FROM matches
) AS carded
GROUP BY club
ORDER BY total_cards DESC
LIMIT 10;
