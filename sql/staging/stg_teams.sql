CREATE SCHEMA IF NOT EXISTS staging;
CREATE OR REPLACE TABLE staging.teams AS

SELECT
    id AS team_id,
    name AS team_name,
    short_name,
    code,
    position AS league_position,
    played,
    win,
    draw,
    loss,
    points,
    strength_overall_home,
    strength_overall_away,
    strength_attack_home,
    strength_attack_away,
    strength_defence_home,
    strength_defence_away

FROM raw.teams;