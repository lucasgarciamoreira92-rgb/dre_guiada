from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.db.session import get_db, make_engine
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def migrated(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")
    engine = make_engine(url)
    yield engine, cfg
    engine.dispose()


@pytest.fixture
def client(migrated):
    engine, _ = migrated
    session = sessionmaker(bind=engine)

    def override():
        with session() as db:
            yield db

    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
