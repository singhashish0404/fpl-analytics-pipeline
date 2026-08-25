#shared way of connecting to DuckDB
import os 
import duckdb
from dotenv import load_dotenv    #loads duckdb python client 

load_dotenv()   #allows python to read .env

DUCKDB_PATH = os.getenv("DUCKDB_PATH","data/fpl_warehouse.duckdb")  #loads DUCKDB_PATH into the environement 

def get_connection():
    return duckdb.connect(DUCKDB_PATH)      #opens duckDB database