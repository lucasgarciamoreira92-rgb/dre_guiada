"""Enable tracked hooks without replacing an existing hook configuration."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
existing = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=root, text=True, capture_output=True).stdout.strip()
if existing and existing != ".githooks":
    raise SystemExit("Hooks existentes preservados: " + existing + ". Integre scripts/validate.py antes de ativar os hooks do projeto.")
hooks = Path(subprocess.check_output(["git", "rev-parse", "--git-path", "hooks"], cwd=root, text=True).strip())
if not hooks.is_absolute():
    hooks = root / hooks
if not existing and hooks.exists() and any(p.is_file() and not p.name.endswith(".sample") for p in hooks.iterdir()):
    raise SystemExit("Hooks locais existentes preservados; revise antes de ativar .githooks.")
subprocess.run(["git", "config", "--local", "core.hooksPath", ".githooks"], cwd=root, check=True)
print("Hooks ativados: validação antes do push e após merge/pull.")
