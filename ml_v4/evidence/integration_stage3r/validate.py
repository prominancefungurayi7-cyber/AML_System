"""Execute restored approved tests; redirect generated evidence to Stage3R."""
import hashlib,json,runpy,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
if '--child' in sys.argv:
    original=Path.write_text
    def redirected(path,data,*args,**kwargs):
        if path.resolve()==(ROOT/'ml_v4/evidence/integration_stage3/parity.json').resolve():
            return original(OUT/'parity.json',data,*args,**kwargs)
        if path.resolve().is_relative_to((ROOT/'ml_v4/evidence/integration_stage3').resolve()):
            raise AssertionError('Historical evidence write prohibited')
        return original(path,data,*args,**kwargs)
    Path.write_text=redirected
    sys.argv=[str(ROOT/'ml_v4/evidence/integration_stage3/run_tests.py'),'--child']
    runpy.run_path(sys.argv[0],run_name='__main__')
else:
    manifest=json.loads((ROOT/'ml_v4/evidence/integration_stage3/decision.json').read_text())
    checks={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in manifest['artifact_sha256']}
    assert checks==manifest['artifact_sha256']
    authority=json.loads((ROOT/'ml_v4/frozen_inference/authority.json').read_text())
    for entry in authority['artifacts'].values():
        assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256']
    (OUT/'source_integrity_gate.json').write_text(json.dumps({'status':'PASS','before_model_deserialization':True,'stage3_artifacts':checks,'frozen_authority':authority['artifacts']},indent=2)+'\n')
    python=ROOT/'ml_v4/.venv_inference_stage3/Scripts/python.exe'
    p=subprocess.run([str(python),'-I','-B',str(Path(__file__).resolve()),'--child'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (OUT/'test_results.txt').write_text(p.stdout,encoding='utf-8')
    print(p.stdout)
    raise SystemExit(p.returncode)
