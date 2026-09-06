#this is unused as of now
import duckdb
import pytest

@pytest.fixture
def test_db():
    con = duckdb.connect(":memory:")  #duckdb in memory so test dont touch fpl_warehouse.duckdb
    yield con 

    con.close()