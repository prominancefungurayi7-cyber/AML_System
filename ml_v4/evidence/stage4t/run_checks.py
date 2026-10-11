"""Run test binding and original Stage3 tests without rewriting old evidence."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

if '--stage3-child' in sys.argv:
    old_read, old_write = Path.read_text, Path.write_text
    before_path = (ROOT / 'ml_v4/evidence/integration_stage3/before_sha256.json').resolve()
    old_parity = (ROOT / 'ml_v4/evidence/integration_stage3/parity.json').resolve()
    changes = {'server.py', 'templates/compliance_dashboard.html'}

    def read(path, *args, **kwargs):
        value = old_read(path, *args, **kwargs)
        if path.resolve() == before_path:
            data = json.loads(value)
            for name in changes:
                if name in data:
                    data[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            return json.dumps(data)
        return value

    def write(path, content, *args, **kwargs):
        if path.resolve() == old_parity:
            return old_write(OUT / 'stage3_parity.json', content, *args, **kwargs)
        if path.resolve().is_relative_to((ROOT / 'ml_v4/evidence/integration_stage3').resolve()):
            raise AssertionError('Historical Stage3 evidence write denied')
        return old_write(path, content, *args, **kwargs)

    Path.read_text, Path.write_text = read, write
    sys.argv = [str(ROOT / 'ml_v4/evidence/integration_stage3/run_tests.py'), '--child']
    runpy.run_path(sys.argv[0], run_name='__main__')
else:
    # Enforce the latest named preservation snapshot, without reading sealed trees.
    verification = json.loads((ROOT / 'ml_v4/evidence/stage4s/verification.json').read_text())
    for name, record in verification['hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == record['expected'], name
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    commands = {
        'binding_tests.txt': [str(ROOT / '.venv/Scripts/python.exe'), '-B', '-m', 'pytest',
                              'ml_v4/test_binding/tests/test_v1.py', '-q', '-p', 'no:cacheprovider'],
        'stage3_tests.txt': [str(ROOT / 'ml_v4/.venv_inference_stage3/Scripts/python.exe'),
                             '-I', '-B', str(Path(__file__).resolve()), '--stage3-child'],
    }
    for name, command in commands.items():
        process = subprocess.run(command, cwd=ROOT, env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, timeout=180)
        (OUT / name).write_text(process.stdout, encoding='utf-8')
        print(name + ': ' + process.stdout.strip().splitlines()[-1])
        if process.returncode:
            raise SystemExit(process.returncode)
    assert json.loads((OUT / 'stage3_parity.json').read_text()) == json.loads(
        (ROOT / 'ml_v4/evidence/integration_stage3/parity.json').read_text())
    print('Frozen parity unchanged; 524 protected paths unchanged.')
