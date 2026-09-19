"""Validation gate for Linux and macOS; logs include commit and actual platform."""
import datetime
import json
import os
import platform
from pathlib import Path
import subprocess
import sys

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
    env.pop("DATABASE_URL", None)
    commands = [
        ("backend", [str(ROOT / "backend/.venv/bin/python"), "-m", "pytest", "-q"]),
        ("frontend", ["npm", "run", "build"]),
        ("frontend", ["npm", "run", "test:e2e"]),
    ]
    code = 1
    try:
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
        report["status"] = "passed" if code == 0 else "failed"
    except Exception as error:
        report.update(status="failed", error=str(error))
        print(error, file=sys.stderr)
        code = 1
    finally:
        target = output / (stamp + ".json")
        target.write_text(json.dumps(report, indent=2) + "\n")
        print("Relatório:", target)
    return code

if __name__ == "__main__":
    sys.exit(main())
