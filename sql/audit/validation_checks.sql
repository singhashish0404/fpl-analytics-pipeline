SELECT
    'players_row_count' AS check_name,
    'staging.players' AS table_name,
    COUNT(*) AS rows_checked,
    CASE
        WHEN COUNT(*) > 0 THEN 0
        ELSE 1
    END AS rows_failed
FROM staging.players

UNION ALL

SELECT
    'duplicate_player_ids',
    'staging.players',
    COUNT(*),
    COUNT(*) - COUNT(DISTINCT player_id)
FROM staging.players

UNION ALL

SELECT
    'null_player_ids',
    'staging.players',
    COUNT(*),
    COUNT(*) FILTER (WHERE player_id IS NULL)
FROM staging.players

UNION ALL

SELECT
    'negative_points',
    'staging.players',
    COUNT(*),
    COUNT(*) FILTER (WHERE total_points < 0)
FROM staging.players

UNION ALL

SELECT
    'rankings_row_count',
    'curated.player_rankings',
    COUNT(*),
    CASE
        WHEN COUNT(*) > 0 THEN 0
        ELSE 1
    END
FROM curated.player_rankings

UNION ALL

SELECT
    'duplicate_rankings_player_ids',
    'curated.player_rankings',
    COUNT(*),
    COUNT(*) - COUNT(DISTINCT player_id)
FROM curated.player_rankings

UNION ALL

SELECT
    'null_team_names',
    'curated.player_rankings',
    COUNT(*),
    COUNT(*) FILTER (WHERE team_name IS NULL)
FROM curated.player_rankings;

