import os

import pytest
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def postgres_engine():
    url = os.getenv("DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        pytest.skip("DATABASE_URL must be PostgreSQL for migration tests")
    engine = create_engine(url)
    yield engine
    engine.dispose()


def test_alembic_upgrade_head_creates_core_tables(postgres_engine):
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    command.upgrade(cfg, "head")

    inspector = inspect(postgres_engine)
    tables = set(inspector.get_table_names())
    expected = {
        "users",
        "documents",
        "document_versions",
        "ingestion_jobs",
        "admin_audit_logs",
        "stripe_processed_events",
    }
    missing = expected - tables
    assert not missing, f"Missing tables after migration: {missing}"
