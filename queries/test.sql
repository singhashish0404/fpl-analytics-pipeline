SELECT
    gameweek,
    COUNT(*) AS rows
FROM raw.gw_live
GROUP BY gameweek
ORDER BY gameweek;