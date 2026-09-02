from datetime import datetime
import uuid
from src.utils.db import get_connection

#create a new pipeline audit record with status = running and return run_id
def start_run(stage,job_type,started_at = None,):
    if started_at is None:
        started_at=datetime.now()

    run_id = str(uuid.uuid4())
    con = get_connection()

    try:
        con.execute(
            """
            INSERT INTO audit.pipeline_runs
            (
                run_id,
                gameweek,
                stage,
                job_type,
                rows_in,
                rows_out,
                rows_rejected,
                status,
                error_message,
                started_at,
                ended_at,
                duration_secs)
            
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                run_id,
                None,
                stage,
                job_type,
                None,
                None,
                0,
                "running",
                None,
                started_at,
                None,
                None,
            ]
        )
    finally:
        con.close()

    return run_id  


#complete an existing pipeline audit record
def finish_run(run_id,status,started_at,rows_in=None,rows_out=None,rows_rejected=0,error=None,):
    ended_at =datetime.now()
    duration = ((ended_at-started_at).total_seconds() if started_at else 0)
    con =get_connection()   

    try:
        con.execute(
            """
            UPDATE audit.pipeline_runs
            SET
                rows_in = ?,
                rows_out = ?,
                rows_rejected = ?,
                status = ?,
                error_message = ?,
                ended_at = ?,
                duration_secs = ?
            WHERE run_id = ?
            """,
            [
                rows_in,
                rows_out,
                rows_rejected,
                status,
                error,
                ended_at,
                duration,
                run_id,
            ],
        )
    finally:
        con.close()

#log the result of one data-quality validation check 
def log_validation(run_id,check_name,table,checked,failed,status,gameweek=None,):

        con =get_connection()
        failure_pct = (round(failed / checked * 100, 2) if checked > 0 else 0)


        log_id = str(uuid.uuid4())

        try:
            con.execute(
                """
                INSERT INTO audit.validation_log
                (
                    log_id,
                    run_id,
                    gameweek,
                    check_name,
                    table_name,
                    rows_checked,
                    rows_failed,
                    failure_pct,
                    check_status,
                    checked_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    log_id,
                    run_id,
                    gameweek,
                    check_name,
                    table,
                    checked,
                    failed,
                    failure_pct,
                    status,
                    datetime.now(),
                ],
            )

        finally:
            con.close()

#determine the severity of validation result
def determine_status(check_name,rows_failed):
    if rows_failed == 0:
        return "pass"

    if check_name == "negative_points":
        return "WARNING"

    return "FAIL"

#execute all validation checks and log their result 
def run_validations(run_id):
    sql_file = "sql/audit/validation_checks.sql"
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    con = get_connection()

    try:
        results = con.execute(sql).fetchall()

    finally:
        con.close()

    for (check_name,table_name,rows_checked,rows_failed,) in results:
        status = determine_status(check_name,rows_failed)
        log_validation(
            run_id=run_id,
            check_name=check_name,
            table=table_name,
            checked=rows_checked,
            failed=rows_failed,
            status=status,
        )

