import os

import duckdb
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DUCKDB_PATH = os.getenv(
    "DUCKDB_PATH",
    "data/fpl_warehouse.duckdb"
)

if not os.path.isabs(DUCKDB_PATH):
    DUCKDB_PATH = os.path.join(PROJECT_ROOT, DUCKDB_PATH)


def get_connection():
    return duckdb.connect(DUCKDB_PATH)