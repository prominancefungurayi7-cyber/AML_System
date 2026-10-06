"""Recorded isolated test execution, without application pytest configuration."""
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
if '--child' in sys.argv:
    sys.path.insert(0,str(ROOT))
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
    import pytest
    raise SystemExit(pytest.main([str(ROOT/'ml_v4/frozen_inference/tests/test_service.py'),'-q','-p','no:cacheprovider','--confcutdir='+str(ROOT/'ml_v4/frozen_inference/tests')]))
p=subprocess.run([sys.executable,'-I','-B',str(Path(__file__).resolve()),'--child'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(Path(__file__).parent/'test_results.txt').write_text(p.stdout,encoding='utf-8')
print(p.stdout)
raise SystemExit(p.returncode)
