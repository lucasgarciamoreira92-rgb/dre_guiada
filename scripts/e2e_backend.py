"""Isolated database for browser tests; never touches the development database."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="dre-e2e-") as directory:
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{directory}/e2e.db"}
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=root / "backend",
        env=env,
        check=True,
    )
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=root / "backend",
            env=env,
            check=True,
        )
    except KeyboardInterrupt:
        pass
