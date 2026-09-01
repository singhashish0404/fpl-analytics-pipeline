from pathlib import Path
from datetime import datetime
import pandas as pd
import json

from src.utils.api import fetch
from src.utils.db import get_connection
from src.utils.logger import get_logger


# Paths
RAW_DIR = Path("data/raw")


# Logger
logger = get_logger(__name__)


def is_stale(filepath, hours=24):
    """
    Return True if the file does not exist
    or is older than the specified number of hours.
    """

    if not filepath.exists():
        return True

    file_age = datetime.now().timestamp() - filepath.stat().st_mtime

    return file_age > hours * 3600


def extract_bootstrap():
    logger.info("Starting bootstrap extraction")

    # Make sure raw directory exists
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    raw_file = RAW_DIR / "bootstrap-static.json"

    # Check whether cached bootstrap data exists
    if is_stale(raw_file):
        logger.info("Bootstrap data is missing or stale")
        logger.info("Fetching fresh bootstrap-static data")

        data = fetch("bootstrap-static")

        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved fresh bootstrap-static data to {raw_file}")

    else:
        logger.info("Using cached bootstrap-static data")

        with open(raw_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    # Connect to DuckDB
    con = get_connection()

    # Create raw schema if it doesn't exist
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # Load source collections into raw tables
    players = pd.DataFrame(data["elements"])
    teams = pd.DataFrame(data["teams"])
    events = pd.DataFrame(data["events"])

    con.execute(
        "CREATE OR REPLACE TABLE raw.players AS SELECT * FROM players"
    )

    con.execute(
        "CREATE OR REPLACE TABLE raw.teams AS SELECT * FROM teams"
    )

    con.execute(
        "CREATE OR REPLACE TABLE raw.events AS SELECT * FROM events"
    )

    logger.info(f"raw.players loaded: {len(players):,} rows")
    logger.info(f"raw.teams loaded: {len(teams):,} rows")
    logger.info(f"raw.events loaded: {len(events):,} rows")

    con.close()

    logger.info("Bootstrap-static extraction complete")

    return data


def extract_fixtures():
    logger.info("Starting fixtures extraction")

    # Make sure raw directory exists
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    raw_file = RAW_DIR / "fixtures.json"

    # Check whether cached fixtures data exists
    if is_stale(raw_file):
        logger.info("Fixtures data is missing or stale")
        logger.info("Fetching fresh fixtures data")

        data = fetch("fixtures")

        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved fresh fixtures data to {raw_file}")

    else:
        logger.info("Using cached fixtures data")

        with open(raw_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    # Connect to DuckDB
    con = get_connection()

    # Create raw schema if it doesn't exist
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # Convert API records to DataFrame
    fixtures = pd.DataFrame(data)

    # Load into DuckDB
    con.execute(
        "CREATE OR REPLACE TABLE raw.fixtures AS SELECT * FROM fixtures"
    )

    logger.info(f"raw.fixtures loaded: {len(fixtures):,} rows")

    con.close()

    logger.info("Fixtures extraction complete")

    return data


def extract_live_gameweeks(bootstrap_data):
    logger.info("Starting live gameweek extraction")

    # Get gameweek information from bootstrap-static
    events = bootstrap_data["events"]

    # Finished gameweeks + current gameweek
    gameweeks = [
        event["id"]
        for event in events
        if event["finished"] or event["is_current"]
    ]

    logger.info(f"Gameweeks identified for extraction: {gameweeks}")

    # Connect to DuckDB
    con = get_connection()

    # Create raw schema if it doesn't exist
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # Check whether the combined table already exists
    table_exists = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'raw'
          AND table_name = 'gw_live'
        """
    ).fetchone()[0] > 0

    for gw in gameweeks:

        # Determine whether this is the current gameweek
        current = next(
            event for event in events
            if event["id"] == gw
        )["is_current"]

        # Finished GW: skip if already extracted
        if table_exists and not current:
            existing = con.execute(
                """
                SELECT COUNT(*)
                FROM raw.gw_live
                WHERE gameweek = ?
                """,
                [gw]
            ).fetchone()[0]

            if existing > 0:
                logger.info(
                    f"GW{gw} already exists in raw.gw_live — skipping"
                )
                continue

        logger.info(f"Fetching live data for GW{gw}")

        # Fetch live gameweek data
        data = fetch(f"event/{gw}/live")

        # Save raw API response
        RAW_DIR.mkdir(parents=True, exist_ok=True)

        raw_file = RAW_DIR / f"live_gw{gw}.json"

        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved raw GW{gw} data to {raw_file}")

        # Flatten only the API's nested stats structure
        elements = pd.DataFrame(
            [
                e["stats"] | {
                    "id": e["id"],
                    "gameweek": gw
                }
                for e in data["elements"]
            ]
        )

        if table_exists:

            # Replace this GW if it already exists
            con.execute(
                """
                DELETE FROM raw.gw_live
                WHERE gameweek = ?
                """,
                [gw]
            )

            con.execute(
                """
                INSERT INTO raw.gw_live
                SELECT * FROM elements
                """
            )

        else:

            # First gameweek creates the table
            con.execute(
                """
                CREATE TABLE raw.gw_live
                AS SELECT * FROM elements
                """
            )

            table_exists = True

        logger.info(
            f"GW{gw} loaded into raw.gw_live: "
            f"{len(elements):,} rows"
        )

    con.close()

    logger.info("Live gameweek extraction complete")


if __name__ == "__main__":

    # Extract bootstrap data once.
    # Cached data is used if it is less than 24 hours old.
    bootstrap_data = extract_bootstrap()

    # Extract fixtures.
    # Cached data is used if it is less than 24 hours old.
    extract_fixtures()

    # Use the same bootstrap data to determine
    # which gameweeks need live extraction.
    extract_live_gameweeks(bootstrap_data)