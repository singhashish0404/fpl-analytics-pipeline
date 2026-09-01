CREATE SCHEMA IF NOT EXISTS staging;
CREATE OR REPLACE TABLE staging.fixtures AS

SELECT
    id AS fixture_id,
    event AS gameweek,
    kickoff_time,
    team_h AS home_team_id,
    team_a AS away_team_id,
    team_h_score AS home_score,
    team_a_score AS away_score,
    team_h_difficulty AS home_difficulty,
    team_a_difficulty AS away_difficulty,
    finished

FROM raw.fixtures;