from pathlib import Path
from src.utils.db import get_connection 
from src.utils.logger import get_logger

STAGING_DIR = Path("sql/staging")
logger = get_logger(__name__)

def run_staging():
    logger.info("Starting staging layer")
    con = get_connection()

    try:
        #creating staging schema if it doesn't exist
        con.execute("CREATE SCHEMA IF NOT EXISTS staging")
        #staging files
        staging_files =[
            "stg_players.sql",
            "stg_teams.sql",
            "stg_fixtures.sql"
        ]

        #execute each staging transformation
        for filenname in staging_files:
            sql_file = STAGING_DIR / filenname
            logger.info(f"Running {sql_file}")

            sql = sql_file.read_text(encoding="utf-8")
            try:
                con.execute(sql)
            except Exception:
                logger.exception(f"Failed while executing {sql_file}")
                raise
            logger.info(f"Completed {filenname}")

        logger.info("staging layer completed succesfully") 

    finally:
        con.close()           

if __name__ == "__main__":
    run_staging()