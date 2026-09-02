from pathlib import Path
from src.utils.db import get_connection
from src.utils.logger import get_logger

SQL_DIR = Path("sql/transform")
logger = get_logger(__name__)


def run_transform():
    logger.info("starting transformation layer")
    sql_file = SQL_DIR / "player_ranking.sql"

    logger.info(f"reading SQL FILE {sql_file}")

    with open(sql_file,"r",encoding="utf-8") as f:
        sql =f.read()

    con = get_connection()

    try:
        con.execute(sql)
        logger.info("Player Rankiing transformation completed successfully")

    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise

    finally:
        con.close()
        logger.info("DuckDB connection closed ")


if __name__ == "__main__":
    run_transform()