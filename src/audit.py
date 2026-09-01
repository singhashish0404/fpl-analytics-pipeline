from datetime import datetime
import uuid
from pathlib import Path
from src.utils.db import get_connection

SQL_DIR = Path("sql/audit")

#Log one pipeline execution into audit.pipeline_runs.
def log_run( stage, job_type, rows_in, rows_out, status, error=None, started_at=None, rows_rejected=0,gameweek=None,):

    con = get_connection()
    ended_at=datetime.now()

    duration= ((ended_at-started_at).total_seconds() if started_at else 0)

    run_id = str(uuid.uuid4())       #creates a unique identifier for each pipeline run.

    con.execute(
        """
        INSERT INTO audit.pipeline_runs
        (
           run_id, gameweek, stage, job_type, rows_in, rows_out, rows_rejected, status, error_message, started_at, ended_at, duration_secs 
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [run_id, gameweek, stage, job_type, rows_in, rows_out, rows_rejected, status, error, started_at, ended_at, duration,],
    )

    con.close()
    return run_id


#log one data validation check into audit.validation_log
def log_validation(run_id, check_name, table, checked, failed, status,gameweek=None,):
    con =get_connection()

    failure_pct = (round(failed/checked *100,2) if checked>0 else 0)
    log_id = str(uuid.uuid4())

    con.execute(
        """
        INSERT INTO audit.validation_log
        (log_id, run_id, gameweek, check_name, table_name, rows_checked, rows_failed, failure_pct, check_status, checked_at)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

        [log_id, run_id, gameweek, check_name, table, checked, failed, failure_pct, status, datetime.now(),],
    )

    con.close()

#determine the audit status for a validation check
def determine_status(check_name,rows_failed):
    if rows_failed==0:
        return "pass"

    #negative points are treated as warning - pipeline shall continue 
    if check_name== "negative_points":
        return "WARNING"

    return "FAIL"

#executing all validation checks and log their results
def run_validations(run_id):
    sql_file = SQL_DIR / "validation_checks.sql"
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    con = get_connection()
    try:
        results = con.execute(sql).fetchall()
    finally:
        con.close()

    for check_name, table_name, rows_checked, rows_failed in results:
        status = determine_status(check_name,rows_failed)

        log_validation(
            run_id=run_id, 
            check_name=check_name, 
            table=table_name, 
            checked=rows_checked,
            failed=rows_failed,
            status=status,
        )

if __name__ == "__main__": 
    started_at = datetime.now() 
    run_id = log_run(  
        stage="audit", 
        job_type="db_to_db", 
        rows_in=0, 
        rows_out=0, 
        rows_rejected=0, 
        status="success", 
        started_at=started_at, 
        ) 

    run_validations(run_id=run_id) 

    print(f"Audit completed. Run ID: {run_id}")