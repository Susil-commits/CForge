"""Global Pytest Fixtures and Environment Bootstrapping."""

from pathlib import Path
import pytest
from cforge.config import ESTATE_DB_PATH, METADATA_DB_PATH
from cforge.estate.loader import init_duckdb_estate
from cforge.catalog.store import MetadataStore


@pytest.fixture(scope="session", autouse=True)
def ensure_cforge_bootstrapped():
    """Ensure the estate database and metadata catalog are initialized for all test suites."""
    if not ESTATE_DB_PATH.exists() or ESTATE_DB_PATH.stat().st_size == 0:
        init_duckdb_estate()

    store = MetadataStore(METADATA_DB_PATH, auto_populate=True)
    count = store.conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    if count == 0:
        store.populate_from_estate()
