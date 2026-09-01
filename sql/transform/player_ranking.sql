CREATE SCHEMA IF NOT EXISTS curated;
CREATE TABLE IF NOT EXISTS curated.player_rankings (
    player_id         INTEGER PRIMARY KEY,
    player_name       VARCHAR,
    team_name         VARCHAR,
    position          VARCHAR,
    price_millions    FLOAT,
    total_points      INTEGER,
    value_score       FLOAT,
    form_rating       FLOAT,
    ownership_pct     FLOAT,
    goals_scored      INTEGER,
    assists           INTEGER,
    pick_category     VARCHAR,
    updated_at        TIMESTAMP
);  

MERGE INTO curated.player_rankings as target
USING (
    SELECT
        p.player_id,
        p.player_name,
        t.team_name,
        p.position,
        p.price_millions,
        p.total_points,
        ROUND(
            p.total_points/ NULLIF(p.price_millions,0),
            2
        ) AS value_score,
        p.form_rating,
        p.ownership_pct,
        p.goals_scored,
        p.assists,

        CASE 
            WHEN p.form_rating > 8.0 
                AND p.ownership_pct <10.0
                THEN 'Premium Differential'

            WHEN p.form_rating > 6.0
                AND p.price_millions < 6.5
                THEN 'Budget Gem'

            WHEN p.total_points > 120
                AND p.ownership_pct > 40.0
                THEN 'Essential Pick'

            WHEN p.form_rating > 7.0
                AND p.ownership_pct > 20.0
                THEN 'Captaincy Candidate'

            ELSE 'Standard'
        END AS pick_category,

        CURRENT_TIMESTAMP AS updated_at   
    FROM staging.players p 
    JOIN staging.teams t
        ON p.team_id = t.team_id
) AS source

ON target.player_id = source.player_id

WHEN MATCHED THEN 
    UPDATE SET 
        value_score   = source.value_score,
        form_rating   = source.form_rating,
        total_points  = source.total_points,
        pick_category = source.pick_category,
        ownership_pct = source.ownership_pct,
        updated_at    = source.updated_at

WHEN NOT MATCHED THEN 
    INSERT VALUES (
        source.player_id,
        source.player_name,
        source.team_name,
        source.position,
        source.price_millions,
        source.total_points,
        source.value_score,
        source.form_rating,
        source.ownership_pct,
        source.goals_scored,
        source.assists,
        source.pick_category,
        source.updated_at
    );