-- Strictly for DuckDB queries
SELECT
    run_id,
    gameweek,
    stage,
    job_type,
    rows_in,
    rows_out,
    rows_rejected,
    status,
    started_at,
    ended_at,
    duration_secs
FROM audit.pipeline_runs
ORDER BY started_at DESC;

SELECT
    run_id,
    check_name,
    table_name,
    rows_checked,
    rows_failed,
    check_status
FROM audit.validation_log
ORDER BY checked_at DESC;