"""Non-destructive validation of the database configured for the application."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.engine import make_url

REQUIRED_TABLES = {"alembic_version", "companies", "periods", "transactions", "subcategories", "period_adjustments"}
ROOT = Path(__file__).resolve().parents[1]


def validate_database(url, report):
    from app.db.session import make_engine

    config = Config(str(ROOT / "backend/alembic.ini"))
    config.attributes["database_url"] = url
    heads = sorted(ScriptDirectory.from_config(config).get_heads())
    parsed = make_url(url)
    report.update(status="failed", expected_heads=heads, current_heads=[], tables=[])
    report["database"] = parsed.render_as_string(hide_password=True)
    if parsed.get_backend_name() == "sqlite":
        if not parsed.database or parsed.database == ":memory:" or not Path(parsed.database).is_file():
            raise RuntimeError("Banco local ausente. Prepare o banco com alembic upgrade head antes da validação; nenhum banco foi recriado.")
    engine = make_engine(url)
    try:
        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
            report["tables"] = sorted(tables)
            report["current_heads"] = sorted(MigrationContext.configure(connection).get_current_heads())
            if "alembic_version" not in tables:
                raise RuntimeError("Tabela obrigatória ausente: alembic_version. Faça backup e corrija o banco local antes de validar.")
        command.upgrade(config, "head")
        with engine.connect() as connection:
            report["current_heads"] = sorted(MigrationContext.configure(connection).get_current_heads())
            report["tables"] = sorted(inspect(connection).get_table_names())
            if report["current_heads"] != heads:
                raise RuntimeError("Banco local não está no head das migrations.")
            missing = REQUIRED_TABLES - set(report["tables"])
            if missing:
                raise RuntimeError("Tabela(s) obrigatória(s) ausente(s): " + ", ".join(sorted(missing)))
        # Also detects stamped databases with missing columns or indexes.
        command.check(config)
        report["status"] = "passed"
        print("Banco local: OK", flush=True)
        print("Alembic: " + ", ".join(heads) + " (head)", flush=True)
    finally:
        engine.dispose()
