import duckdb

from src import transform


def setup_staging_tables(con):
    con.execute("CREATE SCHEMA staging")

    con.execute("""
        CREATE TABLE staging.players (
            player_id INTEGER,
            player_name VARCHAR,
            team_id INTEGER,
            position VARCHAR,
            price_millions FLOAT,
            total_points INTEGER,
            form_rating FLOAT,
            ownership_pct FLOAT,
            goals_scored INTEGER,
            assists INTEGER
        )
    """)

    con.execute("""
        CREATE TABLE staging.teams (
            team_id INTEGER,
            team_name VARCHAR
        )
    """)


def setup_curated_table(con):
    con.execute("CREATE SCHEMA curated")

    con.execute("""
        CREATE TABLE curated.player_rankings (
            player_id INTEGER PRIMARY KEY,
            player_name VARCHAR,
            team_name VARCHAR,
            position VARCHAR,
            price_millions FLOAT,
            total_points INTEGER,
            value_score FLOAT,
            form_rating FLOAT,
            ownership_pct FLOAT,
            goals_scored INTEGER,
            assists INTEGER,
            pick_category VARCHAR,
            updated_at TIMESTAMP
        )
    """)


def test_player_ranking_inserts_new_player(monkeypatch, tmp_path):

    db_path = tmp_path / "test.duckdb"

    con = duckdb.connect(str(db_path))

    setup_staging_tables(con)
    setup_curated_table(con)

    con.execute("""
        INSERT INTO staging.teams VALUES
        (1, 'Test FC')
    """)

    con.execute("""
        INSERT INTO staging.players VALUES
        (
            1,
            'Test Player',
            1,
            'MID',
            5.0,
            100,
            9.0,
            5.0,
            8,
            4
        )
    """)

    con.close()

    monkeypatch.setattr(
        transform,
        "get_connection",
        lambda: duckdb.connect(str(db_path))
    )

    transform.run_transform()

    con = duckdb.connect(str(db_path))

    row = con.execute("""
        SELECT
            player_id,
            player_name,
            team_name,
            value_score,
            pick_category
        FROM curated.player_rankings
    """).fetchone()

    con.close()

    assert row[:3] == (
        1,
        "Test Player",
        "Test FC"
    )

    assert row[3] == 20.0
    assert row[4] == "Premium Differential"


def test_player_ranking_updates_existing_player(monkeypatch, tmp_path):

    db_path = tmp_path / "test.duckdb"

    con = duckdb.connect(str(db_path))

    setup_staging_tables(con)
    setup_curated_table(con)

    con.execute("""
        INSERT INTO staging.teams VALUES
        (1, 'Test FC')
    """)

    # Existing player already in curated table
    con.execute("""
        INSERT INTO curated.player_rankings VALUES
        (
            1,
            'Test Player',
            'Test FC',
            'MID',
            5.0,
            80,
            16.0,
            5.0,
            5.0,
            5,
            2,
            'Standard',
            CURRENT_TIMESTAMP
        )
    """)

    # Updated values arriving from staging
    con.execute("""
        INSERT INTO staging.players VALUES
        (
            1,
            'Test Player',
            1,
            'MID',
            5.0,
            120,
            9.0,
            5.0,
            8,
            4
        )
    """)

    con.close()

    monkeypatch.setattr(
        transform,
        "get_connection",
        lambda: duckdb.connect(str(db_path))
    )

    transform.run_transform()

    con = duckdb.connect(str(db_path))

    rows = con.execute("""
        SELECT
            player_id,
            total_points,
            value_score,
            form_rating,
            pick_category
        FROM curated.player_rankings
    """).fetchall()

    con.close()

    # MERGE should update the existing row,
    # not create a duplicate.
    assert len(rows) == 1

    assert rows[0][0] == 1
    assert rows[0][1] == 120
    assert rows[0][2] == 24.0
    assert rows[0][3] == 9.0
    assert rows[0][4] == "Premium Differential"