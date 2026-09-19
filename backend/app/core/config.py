import os
from pathlib import Path

DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{Path(__file__).resolve().parents[2] / 'dre_guiada.db'}"
)
