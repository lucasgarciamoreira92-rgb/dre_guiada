import pytest
from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


def test_migration_from_zero_and_roundtrip(migrated):
    engine, cfg = migrated
    assert set(inspect(engine).get_table_names()) == {
        "companies",
        "periods",
        "alembic_version",
    }
    assert (
        inspect(engine).get_foreign_keys("periods")[0]["referred_table"] == "companies"
    )
    assert inspect(engine).get_unique_constraints("periods")[0]["column_names"] == [
        "company_id",
        "month",
        "year",
    ]
    command.check(cfg)
    command.downgrade(cfg, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    command.upgrade(cfg, "head")
    assert "periods" in inspect(engine).get_table_names()


def test_database_constraints(migrated):
    engine, _ = migrated
    with engine.begin() as c:
        c.execute(
            text(
                "INSERT INTO companies (id,name,created_at,updated_at) VALUES (1,'Test',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
            )
        )
        c.execute(
            text(
                "INSERT INTO periods (company_id,month,year,created_at) VALUES (1,8,2026,CURRENT_TIMESTAMP)"
            )
        )
    statements = [
        "INSERT INTO periods (company_id,month,year,created_at) VALUES (1,8,2026,CURRENT_TIMESTAMP)",
        "INSERT INTO periods (company_id,month,year,created_at) VALUES (999,8,2026,CURRENT_TIMESTAMP)",
        "INSERT INTO periods (company_id,month,year,created_at) VALUES (1,13,2026,CURRENT_TIMESTAMP)",
        "INSERT INTO periods (company_id,month,year,created_at) VALUES (1,9,1800,CURRENT_TIMESTAMP)",
        "UPDATE periods SET status='invalid'",
        "UPDATE periods SET completion_percentage=101",
        "UPDATE companies SET name='  '",
    ]
    for sql in statements:
        with pytest.raises(IntegrityError):
            with engine.begin() as c:
                c.execute(text(sql))
