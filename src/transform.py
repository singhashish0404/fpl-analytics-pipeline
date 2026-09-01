from pathlib import Path
from src.utils.db import get_connection
from src.utils.logger import get_logger
from datetime import datetime
from src.audit import log_run, run_validations

SQL_DIR = Path("sql/transform")
logger = get_logger(__name__)


def run_transform():
    logger.info("starting transformation layer")
    started_at = datetime.now()
    sql_file = SQL_DIR / "player_ranking.sql"

    logger.info(f"reading SQL FILE {sql_file}")

    with open(sql_file,"r",encoding="utf-8") as f:
        sql =f.read()

    con = get_connection()

    try:
        rows_in = con.execute("SELECT COUNT(*) FROM staging.players").fetchone()[0]
        con.execute(sql)
        rows_out = con.execute("SELECT COUNT(*) FROM curated.player_rankings").fetchone()[0]

        run_id = log_run(
            stage="transform",
            job_type="db_to_db",
            rows_in=rows_in,
            rows_out=rows_out,
            rows_rejected=0,
            status="success",
            started_at=started_at
        )

        run_validations(run_id=run_id)

        logger.info("Player Rankiing transformation completed successfully")

    except Exception as e:
        log_run(
            gameweek=1,
            stage="transform",
            job_type="db_to_db",
            rows_in=0,
            rows_out=0,
            rows_rejected=0,
            status="failed",
            error=str(e),
            started_at=started_at
        )

        logger.error(f"Transformation failed: {e}")

        raise

    finally:
        con.close()
        logger.info("DuckDB connection closed ")


if __name__ == "__main__":
    run_transform()