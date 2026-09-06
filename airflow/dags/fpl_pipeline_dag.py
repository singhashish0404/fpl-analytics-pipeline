from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.empty import EmptyOperator

from src.audit import start_run, finish_run, run_validations
from src.extract import (
    extract_bootstrap,
    extract_fixtures,
    extract_live_gameweeks,
)
from src.staging import run_staging
from src.transform import run_transform


def start_pipeline(**context):
    started_at = datetime.now()

    run_id = start_run(
        stage="pipeline",
        job_type="full_pipeline",
        started_at=started_at,
    )

    context["ti"].xcom_push(
        key="run_id",
        value=run_id,
    )

    context["ti"].xcom_push(
        key="started_at",
        value=started_at.isoformat(),
    )


def extract_task():
    bootstrap_data = extract_bootstrap()

    extract_fixtures()

    extract_live_gameweeks(bootstrap_data)


def staging_task():
    run_staging()


def transform_task():
    run_transform()


def validate_task(**context):
    run_id = context["ti"].xcom_pull(
        task_ids="start_pipeline",
        key="run_id",
    )

    run_validations(run_id=run_id)


def finish_pipeline(**context):
    run_id = context["ti"].xcom_pull(
        task_ids="start_pipeline",
        key="run_id",
    )

    started_at_str = context["ti"].xcom_pull(
        task_ids="start_pipeline",
        key="started_at",
    )

    if not run_id or not started_at_str:
        print("No pipeline audit record found. Skipping audit completion.")
        return

    started_at = datetime.fromisoformat(started_at_str)

    task_states = context["ti"].get_task_states(
        dag_id=context["ti"].dag_id
    )

    current_run_id = context["dag_run"].run_id

    current_run_states = task_states.get(current_run_id, {})

    print(f"CURRENT RUN STATES: {current_run_states}")

    pipeline_tasks = [
        "extract",
        "staging",
        "transform",
        "validate",
    ]

    failed_tasks = [
        task_id
        for task_id in pipeline_tasks
        if current_run_states.get(task_id) != "success"
    ]

    if failed_tasks:
        finish_run(
            run_id=run_id,
            status="failed",
            started_at=started_at,
            error=f"Failed tasks: {', '.join(failed_tasks)}",
        )
    else:
        finish_run(
            run_id=run_id,
            status="success",
            started_at=started_at,
        )


def failure_alert(context):
    task_id = context["task_instance"].task_id
    dag_id = context["dag"].dag_id

    print(
        f"ALERT: Task {task_id} in DAG {dag_id} failed. "
        "Check Airflow logs."
    )


default_args = {
    "owner": "ash",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": failure_alert,
}


with DAG(
    dag_id="fpl_analytics_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["fpl", "elt", "duckdb"],
    doc_md="""
    # FPL Analytics ELT Pipeline

    Orchestrates the complete FPL ELT pipeline:

    API → Raw → Staging → Transform → Validation → Audit
    """,
) as dag:

    start = PythonOperator(
        task_id="start_pipeline",
        python_callable=start_pipeline,
    )

    extract = PythonOperator(
        task_id="extract",
        python_callable=extract_task,
    )

    staging = PythonOperator(
        task_id="staging",
        python_callable=staging_task,
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform_task,
    )

    validate = PythonOperator(
        task_id="validate",
        python_callable=validate_task,
    )

    finish = PythonOperator(
        task_id="finish_pipeline",
        python_callable=finish_pipeline,
        trigger_rule="all_done",
    )

    done = EmptyOperator(
        task_id="pipeline_complete",
    )

    start >> extract >> staging >> transform >> validate >> finish >> done