"""Validation gate for Linux and macOS; logs include commit and actual platform."""
import datetime
import json
import os
import platform
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.core.config import DATABASE_URL
from local_database import validate_database

ROOT = Path(__file__).resolve().parents[1]

def main():
    output = ROOT / "validation-results"
    output.mkdir(exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    report = {"time_utc": stamp, "platform": platform.platform(), "machine": platform.machine(),
              "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)),
              "status": "running", "steps": []}
    env = os.environ.copy()
    screenshots = output / "screenshots" / stamp
    env["DRE_SCREENSHOT_DIR"] = str(screenshots)
    report["local_database"] = {}
    report["screenshots"] = {"count": 0, "paths": [], "viewport": {"width": 1440, "height": 900}}
    commands = [
        ("backend", [str(ROOT / "backend/.venv/bin/python"), "-m", "pytest", "-q"]),
        ("frontend", ["npm", "run", "build"]),
        ("frontend", ["npm", "run", "test:e2e"]),
    ]
    code = 1
    try:
        print("Ambiente:", platform.platform(), "Python", platform.python_version(), flush=True)
        subprocess.run(["node", "--version"], check=True)
        subprocess.run(["npm", "--version"], check=True)
        # Resolve relative DATABASE_URL exactly as the local backend (cwd backend).
        os.chdir(ROOT / "backend")
        validate_database(DATABASE_URL, report["local_database"])
        with (output / (stamp + ".log")).open("w") as log:
            for directory, command in commands:
                print("Executando:", " ".join(command), flush=True)
                step = {"command": command, "directory": directory}
                report["steps"].append(step)
                with subprocess.Popen(command, cwd=ROOT / directory, env=env,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as process:
                    for line in process.stdout:
                        print(line, end="", flush=True)
                        log.write(line)
                    code = process.wait()
                step["exit_code"] = code
                if code:
                    break
        if code == 0:
            expected = ["01-welcome", "02-company-period", "03-overview", "04-revenues", "05-expenses", "06-adjustments", "07-dre", "08-settings"]
            for name in expected:
                path = screenshots / (name + ".png")
                if not path.is_file() or path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                    raise RuntimeError(f"Screenshot obrigatório ausente ou inválido: {path}")
            print("Backend tests: OK\nFrontend build: OK\nE2E: OK\nScreenshots: OK (8)")
        report["status"] = "passed" if code == 0 else "failed"
    except Exception as error:
        report.update(status="failed", error=str(error))
        print(error, file=sys.stderr)
        if report["local_database"].get("status") == "failed":
            report["local_database"]["error"] = str(error)
            print("Faça backup e corrija o banco/configuração antes de validar novamente. Nenhuma rotina de restauração ou exclusão foi executada.", file=sys.stderr)
        code = 1
    finally:
        paths = sorted(str(p.relative_to(ROOT)) for p in screenshots.glob("*.png"))
        report["screenshots"].update(count=len(paths), paths=paths)
        target = output / (stamp + ".json")
        target.write_text(json.dumps(report, indent=2) + "\n")
        print("Relatório:", target)
    return code

if __name__ == "__main__":
    sys.exit(main())
