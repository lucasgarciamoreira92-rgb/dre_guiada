"""Run real headed Chromium against an isolated DB, preserving local data."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.core.config import DATABASE_URL
from sqlalchemy.engine import make_url


def snapshot():
    url = make_url(DATABASE_URL)
    if url.get_backend_name() != 'sqlite' or not url.database:
        raise RuntimeError('A validação visual exige um banco local SQLite persistente.')
    path = Path(url.database)
    if not path.is_absolute():
        path = ROOT / 'backend' / path
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as connection:
        integrity = connection.execute('PRAGMA integrity_check').fetchall()
        foreign_keys = connection.execute('PRAGMA foreign_key_check').fetchall()
        if integrity != [('ok',)] or foreign_keys:
            raise RuntimeError(f'Integridade inválida: {integrity}, {foreign_keys}')
        dump = '\n'.join(connection.iterdump()).encode()
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        counts = {name: connection.execute('SELECT COUNT(*) FROM "' + name.replace('"', '""') + '"').fetchone()[0] for name in tables}
    return dict(path=str(path), integrity='ok', foreign_keys=foreign_keys, sha256=hashlib.sha256(dump).hexdigest(), counts=counts)


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    directory = ROOT / 'validation-results' / 'visual' / stamp
    directory.mkdir(parents=True)
    report = dict(platform=platform.platform(), headed=True, status='failed',
                  commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  node=subprocess.check_output(['node', '--version'], text=True).strip())
    code = 1
    try:
        report['before'] = snapshot()
        env = {**os.environ, 'DRE_VISUAL_DIR': str(directory)}
        with (directory / 'run.log').open('w') as log:
            with subprocess.Popen(['npx', 'playwright', 'test', '--config', 'playwright.visual.config.ts'], cwd=ROOT / 'frontend', env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as process:
                for line in process.stdout:
                    print(line, end='', flush=True)
                    log.write(line)
                code = process.wait()
        report['playwright_exit_code'] = code
        report['after'] = snapshot()
        if report['before'] != report['after']:
            raise RuntimeError('O banco persistente mudou durante a validação.')
        report['screenshots'] = [str(path) for path in sorted(directory.glob('*.png'))]
        report['videos'] = [str(path) for path in directory.rglob('*.webm')]
        if code == 0 and (len(report['screenshots']) != 16 or not report['videos']):
            raise RuntimeError('Evidências visuais incompletas.')
        if code == 0:
            traces = list(directory.rglob('trace.zip'))
            if not traces:
                raise RuntimeError('Trace ausente.')
            for trace in traces:
                with zipfile.ZipFile(trace) as archive:
                    if archive.testzip() is not None:
                        raise RuntimeError('Trace corrompido.')
            report['traces'] = [str(path) for path in traces]
        report['status'] = 'passed' if code == 0 else 'failed'
    except Exception as error:
        report['error'] = str(error)
        print(error, file=sys.stderr)
        code = 1
    finally:
        report['exit_code'] = code
        (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print('Relatório:', directory / 'report.json')
    return code


if __name__ == '__main__':
    sys.exit(main())
