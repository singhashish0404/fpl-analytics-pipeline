from src.extract import extract_bootstrap,extract_live_gameweeks,extract_fixtures
from src.staging import run_staging
from src.transform import run_transform
from src.utils.logger import get_logger
from src.audit import start_run, finish_run, run_validations
from datetime import datetime

logger = get_logger(__name__)
def main():
    started_at =datetime.now()
    logger.info("Starting FPL pipeline")
    run_id = start_run(stage="pipeline",job_type="full_pipeline",started_at=started_at,)

    try:

        #extraction - 
        logger.info("STARTED EXTRACTION LAYER")

        bootstrap_data = extract_bootstrap()
        extract_fixtures()
        extract_live_gameweeks(bootstrap_data)

        logger.info("EXTRACTION LAYER COMPLETED")

        #staging -
        logger.info("STARTED STAGING LAYER")
        run_staging()
        logger.info("STAGING LAYER COMPLETED")

        #tranformation - 

        logger.info("STARTING TRANFORMATION LAYER")
        run_transform()
        logger.info("TRANSFORMATION LAYER COMPLETED")

        #validation
        logger.info("STARTED PIPELINE VALIDATION")
        run_validations(run_id=run_id)
        logger.info("PIPELINE VALIDATION COMPLETED")

        #succesful completion
        finish_run(
            run_id=run_id,
            status="success",
            started_at=started_at,
            rows_in=None,
            rows_out=None,
            rows_rejected=0,
        )

        logger.info("FPL PIPELINE RUN SUCCESFUL")

    except Exception as e:
        finish_run(
            run_id=run_id,
            status="failed",
            started_at=started_at,
            rows_in=None,
            rows_out=None,
            rows_rejected=0,
            error=str(e),
        )
        logger.info(f"FPL PIPELINE FAILED : {e}")

        raise

if __name__=="__main__":
    main()