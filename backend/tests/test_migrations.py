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
        "transactions",
        "subcategories",
        "period_adjustments",
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


def test_upgrade_existing_company_preserves_foundation(tmp_path):
    from pathlib import Path
    from alembic.config import Config
    from app.db.session import make_engine

    cfg = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    url = f"sqlite:///{tmp_path / 'existing.db'}"
    cfg.attributes['database_url'] = url
    command.upgrade(cfg, '0001')
    engine = make_engine(url)
    with engine.begin() as c:
        c.execute(text("INSERT INTO companies (id,name,created_at,updated_at) VALUES (1,'Existente',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
        c.execute(text("INSERT INTO periods (id,company_id,month,year,created_at) VALUES (1,1,8,2026,CURRENT_TIMESTAMP)"))
    command.upgrade(cfg, 'head')
    with engine.connect() as c:
        assert c.execute(text('SELECT name FROM companies')).scalar_one() == 'Existente'
        assert c.execute(text('SELECT COUNT(*) FROM subcategories')).scalar_one() == 20
        assert c.execute(text('SELECT month FROM periods')).scalar_one() == 8
        assert c.execute(text('SELECT COUNT(*) FROM transactions')).scalar_one() == 0
    command.upgrade(cfg, 'head')
    command.check(cfg)
    with engine.connect() as c:
        assert c.execute(text('SELECT COUNT(*) FROM subcategories')).scalar_one() == 20
    command.downgrade(cfg, '0001')
    with engine.connect() as c:
        assert c.execute(text('SELECT name FROM companies')).scalar_one() == 'Existente'
    engine.dispose()


def test_m3_upgrade_preserves_m2_transactions_and_roundtrip(tmp_path):
    from pathlib import Path
    from alembic.config import Config
    from app.db.session import make_engine

    cfg = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    url = f"sqlite:///{tmp_path / 'm2.db'}"
    cfg.attributes['database_url'] = url
    command.upgrade(cfg, '0002')
    engine = make_engine(url)
    with engine.begin() as c:
        c.execute(text("INSERT INTO companies (id,name,created_at,updated_at) VALUES (1,'Existente',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
        c.execute(text("INSERT INTO periods (id,company_id,month,year,created_at) VALUES (1,1,8,2026,CURRENT_TIMESTAMP)"))
        c.execute(text("""INSERT INTO transactions
            (id,company_id,period_id,direction,transaction_date,competence_month,competence_year,competence_status,
             competence_source,description,original_description,amount,main_category,dre_effect,classification_status,
             include_in_dre,origin_type,created_at,updated_at)
            VALUES (1,1,1,'IN','2026-09-05',8,2026,'CONFIRMED','USER','Mensalidades','Mensalidades',10000000,
                    'REVENUE_RECURRING','GROSS_REVENUE','CONFIRMED',1,'MANUAL',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"""))
    command.upgrade(cfg, 'head')
    command.check(cfg)
    with engine.connect() as c:
        assert c.execute(text('SELECT amount FROM transactions')).scalar_one() == 10000000
        assert c.execute(text('SELECT competence_month FROM transactions')).scalar_one() == 8
        assert c.execute(text('SELECT COUNT(*) FROM period_adjustments')).scalar_one() == 0
    command.downgrade(cfg, '0002')
    command.upgrade(cfg, 'head')
    with engine.connect() as c:
        assert c.execute(text('SELECT COUNT(*) FROM transactions')).scalar_one() == 1
    engine.dispose()
