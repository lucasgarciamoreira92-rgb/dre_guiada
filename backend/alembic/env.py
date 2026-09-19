from alembic import context
from app.core.config import DATABASE_URL
from app.db.session import Base, make_engine
from app.models import manual  # noqa: F401
from app.models import entities  # noqa: F401 — registers metadata for Alembic

config = context.config
url = config.attributes.get("database_url", DATABASE_URL)
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(url)
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=Base.metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
