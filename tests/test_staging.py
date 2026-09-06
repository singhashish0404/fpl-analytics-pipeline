import duckdb
import pytest

from src import staging


@pytest.fixture
def staging_db(tmp_path):
    db_path = tmp_path / "test.duckdb"

    con = duckdb.connect(str(db_path))

    con.execute("CREATE SCHEMA raw")

    # Raw players table
    con.execute("""
        CREATE TABLE raw.players (
            id INTEGER,
            web_name VARCHAR,
            first_name VARCHAR,
            second_name VARCHAR,
            team INTEGER,
            element_type INTEGER,
            now_cost INTEGER,
            total_points INTEGER,
            form VARCHAR,
            points_per_game VARCHAR,
            selected_by_percent VARCHAR,
            goals_scored INTEGER,
            assists INTEGER,
            clean_sheets INTEGER,
            minutes INTEGER,
            bonus INTEGER,
            yellow_cards INTEGER,
            red_cards INTEGER,
            transfers_in_event INTEGER,
            transfers_out_event INTEGER,
            value_season VARCHAR
        )
    """)

    # Raw teams table
    con.execute("""
        CREATE TABLE raw.teams (
            id INTEGER,
            name VARCHAR,
            short_name VARCHAR,
            code INTEGER,
            position INTEGER,
            played INTEGER,
            win INTEGER,
            draw INTEGER,
            loss INTEGER,
            points INTEGER,
            strength_overall_home INTEGER,
            strength_overall_away INTEGER,
            strength_attack_home INTEGER,
            strength_attack_away INTEGER,
            strength_defence_home INTEGER,
            strength_defence_away INTEGER
        )
    """)

    # Raw fixtures table
    con.execute("""
        CREATE TABLE raw.fixtures (
            id INTEGER,
            event INTEGER,
            kickoff_time TIMESTAMP,
            team_h INTEGER,
            team_a INTEGER,
            team_h_score INTEGER,
            team_a_score INTEGER,
            team_h_difficulty INTEGER,
            team_a_difficulty INTEGER,
            finished BOOLEAN
        )
    """)

    con.close()

    return db_path


def test_staging_players_transforms_and_filters(
    monkeypatch,
    staging_db
):
    con = duckdb.connect(str(staging_db))

    con.execute("""
        INSERT INTO raw.players VALUES
        (
            1, 'Test', 'John', 'Doe',
            1, 2, 55, 100, '5.5', '6.25', '10.5',
            5, 3, 8, 900, 10, 1, 0, 100, 50, '18.2'
        ),
        (
            2, 'Unused', 'Jane', 'Doe',
            1, 3, 60, 0, '0.0', '0.0', '1.0',
            0, 0, 0, 0, 0, 0, 0, 10, 20, '0.0'
        )
    """)

    con.close()

    monkeypatch.setattr(
        staging,
        "get_connection",
        lambda: duckdb.connect(str(staging_db))
    )

    staging.run_staging()

    con = duckdb.connect(str(staging_db))

    rows = con.execute("""
        SELECT
            player_id,
            full_name,
            position,
            price_millions,
            form_rating,
            pints_per_game
        FROM staging.players
        ORDER BY player_id
    """).fetchall()

    con.close()

    assert rows == [
        (1, "John Doe", "DEF", 5.5, 5.5, 6.25)
    ]


def test_staging_teams_maps_columns(
    monkeypatch,
    staging_db
):
    con = duckdb.connect(str(staging_db))

    con.execute("""
        INSERT INTO raw.teams VALUES
        (
            1, 'Test FC', 'TST', 123, 5,
            10, 6, 2, 2, 20,
            1200, 1100, 1150, 1050, 1250, 1150
        )
    """)

    con.close()

    monkeypatch.setattr(
        staging,
        "get_connection",
        lambda: duckdb.connect(str(staging_db))
    )

    staging.run_staging()

    con = duckdb.connect(str(staging_db))

    row = con.execute("""
        SELECT
            team_id,
            team_name,
            short_name,
            league_position,
            points
        FROM staging.teams
    """).fetchone()

    con.close()

    assert row == (
        1,
        "Test FC",
        "TST",
        5,
        20
    )


def test_staging_fixtures_maps_columns(
    monkeypatch,
    staging_db
):
    con = duckdb.connect(str(staging_db))

    con.execute("""
        INSERT INTO raw.fixtures VALUES
        (
            100,
            5,
            '2026-09-01 15:00:00',
            1,
            2,
            3,
            1,
            4,
            2,
            true
        )
    """)

    con.close()

    monkeypatch.setattr(
        staging,
        "get_connection",
        lambda: duckdb.connect(str(staging_db))
    )

    staging.run_staging()

    con = duckdb.connect(str(staging_db))

    row = con.execute("""
        SELECT
            fixture_id,
            gameweek,
            home_team_id,
            away_team_id,
            home_score,
            away_score,
            finished
        FROM staging.fixtures
    """).fetchone()

    con.close()

    assert row == (
        100,
        5,
        1,
        2,
        3,
        1,
        True
    )