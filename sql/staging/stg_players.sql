CREATE SCHEMA IF NOT EXISTS staging;
CREATE OR REPLACE TABLE staging.players as 

SELECT 
    id as player_id,
    web_name as player_name,
    first_name || ' ' || second_name as full_name,
    team AS team_id,
    element_type AS position_id,
    CASE element_type
        WHEN 1 THEN 'GKP'
        WHEN 2 THEN 'DEF'
        WHEN 3 THEN 'MID'
        WHEN 4 THEN 'FWD'
    END AS position,
    ROUND(now_cost/10.0,1) as price_millions,
    total_points,
    CAST(form as FLOAT) AS form_rating,
    ROUND(CAST(points_per_game as FLOAT),2) AS pints_per_game,
    CAST(selected_by_percent AS FLOAT) AS ownership_pct,
    goals_scored,
    assists,
    clean_sheets,
    minutes,
    bonus,
    yellow_cards,
    red_cards,
    transfers_in_event AS gw_transfers_in,
    transfers_out_event AS gw_transfers_out,
    CAST(value_season AS FLOAT) AS value_season

FROM raw.players
WHERE minutes > 0;

