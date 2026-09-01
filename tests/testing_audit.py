from src.audit import log_run, run_validations
from datetime import datetime


started_at = datetime.now()

run_id = log_run(
    gameweek=1,
    stage="audit",
    job_type="db_to_db",
    rows_in=0,
    rows_out=0,
    rows_rejected=0,
    status="success",
    started_at=started_at
)

print("Run ID:", run_id)

run_validations(
    run_id=run_id,
    gameweek=1
)

print("All validation checks completed")