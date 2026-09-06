from src import extract
import time
import duckdb
import pytest


def test_is_stale_when_file_does_not_exist(tmp_path):
    file_path = tmp_path / "test.json"

    assert extract.is_stale(file_path) is True


def test_is_stale_when_file_is_fresh(tmp_path):
    file_path = tmp_path / "test.json"
    file_path.write_text("test")

    assert extract.is_stale(file_path, hours=24) is False


def test_is_stale_when_file_is_old(tmp_path):
    file_path = tmp_path / "test.json"
    file_path.write_text("test")

    old_time = time.time() - (25 * 3600)
    import os
    os.utime(file_path, (old_time, old_time))

    assert extract.is_stale(file_path, hours=24) is True


def test_extract_bootstrap_loads_raw_tables(monkeypatch, tmp_path):
    fake_data = {
        "elements": [
            {
                "id": 1,
                "first_name": "Test",
                "second_name": "Player"
            }
        ],
        "teams": [
            {
                "id": 1,
                "name": "Test Team"
            }
        ],
        "events": [
            {
                "id": 1,
                "name": "Gameweek 1"
            }
        ]
    }

    db_path = tmp_path / "test.duckdb"

    monkeypatch.setattr(
        extract,
        "fetch",
        lambda endpoint: fake_data
    )

    monkeypatch.setattr(
        extract,
        "get_connection",
        lambda: duckdb.connect(str(db_path))
    )

    monkeypatch.setattr(
        extract,
        "RAW_DIR",
        tmp_path
    )

    monkeypatch.setattr(
        extract,
        "is_stale",
        lambda filepath, hours=24: True
    )

    result = extract.extract_bootstrap()

    assert result == fake_data

    con = duckdb.connect(str(db_path))

    players = con.execute(
        "SELECT * FROM raw.players"
    ).fetchall()

    teams = con.execute(
        "SELECT * FROM raw.teams"
    ).fetchall()

    events = con.execute(
        "SELECT * FROM raw.events"
    ).fetchall()

    assert len(players) == 1
    assert len(teams) == 1
    assert len(events) == 1

    con.close()

    assert (tmp_path / "bootstrap-static.json").exists()

def test_extract_bootstrap_uses_cached_data(monkeypatch, tmp_path):
    cached_data = {
        "elements": [
            {
                "id": 1,
                "first_name": "Cached",
                "second_name": "Player"
            }
        ],
        "teams": [
            {
                "id": 1,
                "name": "Cached Team"
            }
        ],
        "events": [
            {
                "id": 1,
                "name": "Gameweek 1"
            }
        ]
    }

    db_path = tmp_path / "test.duckdb"
    raw_file = tmp_path / "bootstrap-static.json"

    with open(raw_file, "w", encoding="utf-8") as f:
        import json
        json.dump(cached_data, f)

    def fail_if_called(endpoint):
        pytest.fail("API should not be called when cached data is fresh")

    monkeypatch.setattr(
        extract,
        "fetch",
        fail_if_called
    )

    monkeypatch.setattr(
        extract,
        "get_connection",
        lambda: duckdb.connect(str(db_path))
    )

    monkeypatch.setattr(
        extract,
        "RAW_DIR",
        tmp_path
    )

    monkeypatch.setattr(
        extract,
        "is_stale",
        lambda filepath, hours=24: False
    )

    result = extract.extract_bootstrap()

    assert result == cached_data

    con = duckdb.connect(str(db_path))

    players = con.execute(
        "SELECT * FROM raw.players"
    ).fetchall()

    assert len(players) == 1
    assert players[0][0] == 1

    con.close()    


def test_extract_live_gameweeks_loads_data(monkeypatch, tmp_path):
    bootstrap_data = {
        "events": [
            {
                "id": 1,
                "finished": True,
                "is_current": False
            },
            {
                "id": 2,
                "finished": False,
                "is_current": True
            },
            {
                "id": 3,
                "finished": False,
                "is_current": False
            }
        ]
    }

    live_data = {
        "elements": [
            {
                "id": 1,
                "stats": {
                    "total_points": 10,
                    "minutes": 90
                }
            },
            {
                "id": 2,
                "stats": {
                    "total_points": 5,
                    "minutes": 60
                }
            }
        ]
    }

    db_path = tmp_path / "test.duckdb"

    def fake_fetch(endpoint):
        return live_data

    monkeypatch.setattr(
        extract,
        "fetch",
        fake_fetch
    )

    monkeypatch.setattr(
        extract,
        "get_connection",
        lambda: duckdb.connect(str(db_path))
    )

    monkeypatch.setattr(
        extract,
        "RAW_DIR",
        tmp_path
    )

    extract.extract_live_gameweeks(bootstrap_data)

    con = duckdb.connect(str(db_path))

    rows = con.execute(
        """
        SELECT id, gameweek, total_points, minutes
        FROM raw.gw_live
        ORDER BY gameweek, id
        """
    ).fetchall()

    con.close()

    assert len(rows) == 4

    assert rows[0] == (1, 1, 10, 90)
    assert rows[1] == (2, 1, 5, 60)

    assert rows[2] == (1, 2, 10, 90)
    assert rows[3] == (2, 2, 5, 60)

    assert (tmp_path / "live_gw1.json").exists()
    assert (tmp_path / "live_gw2.json").exists()

    assert not (tmp_path / "live_gw3.json").exists()    

def test_extract_live_gameweeks_skips_existing_historical_gameweek(
    monkeypatch, tmp_path
):
    bootstrap_data = {
        "events": [
            {
                "id": 1,
                "finished": True,
                "is_current": False
            }
        ]
    }

    db_path = tmp_path / "test.duckdb"

    con = duckdb.connect(str(db_path))

    con.execute("CREATE SCHEMA raw")

    con.execute(
        """
        CREATE TABLE raw.gw_live (
            id INTEGER,
            gameweek INTEGER,
            total_points INTEGER,
            minutes INTEGER
        )
        """
    )

    con.execute(
        """
        INSERT INTO raw.gw_live
        VALUES (1, 1, 10, 90)
        """
    )

    con.close()

    def fail_if_called(endpoint):
        pytest.fail(
            "API should not be called for an existing historical gameweek"
        )

    monkeypatch.setattr(
        extract,
        "fetch",
        fail_if_called
    )

    monkeypatch.setattr(
        extract,
        "get_connection",
        lambda: duckdb.connect(str(db_path))
    )

    monkeypatch.setattr(
        extract,
        "RAW_DIR",
        tmp_path
    )

    extract.extract_live_gameweeks(bootstrap_data)

    con = duckdb.connect(str(db_path))

    rows = con.execute(
        """
        SELECT id, gameweek, total_points, minutes
        FROM raw.gw_live
        """
    ).fetchall()

    con.close()

    assert rows == [(1, 1, 10, 90)]    