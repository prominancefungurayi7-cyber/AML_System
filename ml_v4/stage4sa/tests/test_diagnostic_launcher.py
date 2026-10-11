"""Offline launcher regression; never opens MySQL or submits a fixture."""
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
LAUNCHER = ROOT / 'ml_v4/stage4sa/diagnose_live.ps1'


def test_launcher_module_binding_and_cleanup():
    source = LAUNCHER.read_text(encoding='utf-8')
    assert 'Push-Location $root' in source
    assert '& $python -B -m ml_v4.stage4sa.diagnose_live' in source
    assert '& $python -I -B ml_v4/stage4sa/diagnose_live.py' not in source
    assert "Read-Host 'Password for v4_stage4t_runner on disposable MySQL only' -AsSecureString" in source
    assert 'mysql://v4_stage4t_runner:$encoded@127.0.0.1:3306/v4_stage4s_disposable' in source
    assert "d441b7bb-43f6-11f1-a2d8-0a0027000005" in source
    assert '& $python -I -B ml_v4/test_binding/v1.py check' in source
    assert 'ZeroFreeBSTR($ptr)' in source
    assert 'Remove-Item Env:V4_STAGE4T_TEST_DB_URL' in source
    assert 'Remove-Item Env:V4_STAGE4T_EXPECTED_SERVER_UUID' in source


def test_module_import_reaches_binding_without_credentials():
    env = os.environ.copy()
    env.pop('V4_STAGE4T_TEST_DB_URL', None)
    env.pop('V4_STAGE4T_EXPECTED_SERVER_UUID', None)
    completed = subprocess.run(
        [sys.executable, '-B', '-m', 'ml_v4.stage4sa.diagnose_live'],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=20,
    )
    assert completed.returncode == 1
    assert 'Read-only diagnosis stopped: BindingError' in completed.stdout
    assert 'ModuleNotFoundError' not in completed.stdout + completed.stderr
