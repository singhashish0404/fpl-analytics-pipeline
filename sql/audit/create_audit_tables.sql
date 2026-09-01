CREATE SCHEMA IF NOT EXISTS audit;

--pipeline run log table
CREATE TABLE IF NOT EXISTS audit.pipeline_runs(
    run_id VARCHAR DEFAULT gen_random_uuid(),   -- database itself can generate an ID when one isn't supplied - for more see audit.py
    gameweek        INTEGER,
    stage           VARCHAR,
    job_type        VARCHAR,
    rows_in         INTEGER,
    rows_out        INTEGER,
    rows_rejected   INTEGER,
    status          VARCHAR,
    error_message   VARCHAR,
    started_at      TIMESTAMP,
    ended_at        TIMESTAMP,
    duration_secs   FLOAT
);

-- Table 2: Data validation audit
CREATE TABLE IF NOT EXISTS audit.validation_log (
    log_id          VARCHAR DEFAULT gen_random_uuid(),
    run_id          VARCHAR,
    gameweek        INTEGER,
    check_name      VARCHAR,
    table_name      VARCHAR,
    rows_checked    INTEGER,
    rows_failed     INTEGER,
    failure_pct     DECIMAL(5,2),
    check_status    VARCHAR,
    checked_at      TIMESTAMP
);