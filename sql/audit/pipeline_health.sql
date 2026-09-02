SELECT
    run_id,
    check_name,
    table_name,
    rows_checked,
    rows_failed,
    failure_pct,
    check_status
FROM audit.validation_log
ORDER BY checked_at DESC
LIMIT 10;