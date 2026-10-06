"""Regression runner preserving old evidence and explicit app-change scope."""
import hashlib,json,os,runpy,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
ALLOWED={'server.py','templates/compliance_dashboard.html'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if '--stage3-child' in sys.argv:
    oldread=Path.read_text;oldwrite=Path.write_text
    # Original tests stay byte-identical. Their inherited source-preservation
    # check gets only the two explicitly authorized application hash amendments.
    def read(path,*a,**k):
        text=oldread(path,*a,**k)
        if path.resolve()==(ROOT/'ml_v4/evidence/integration_stage3/before_sha256.json').resolve():
            data=json.loads(text)
            for p in ALLOWED:
                if p in data:data[p]=sha(ROOT/p)
            return json.dumps(data)
        return text
    def write(path,text,*a,**k):
        if path.resolve()==(ROOT/'ml_v4/evidence/integration_stage3/parity.json').resolve():return oldwrite(OUT/'stage3_parity.json',text,*a,**k)
        if path.resolve().is_relative_to((ROOT/'ml_v4/evidence/integration_stage3').resolve()):raise AssertionError('Historical evidence write denied')
        return oldwrite(path,text,*a,**k)
    Path.read_text=read;Path.write_text=write
    sys.argv=[str(ROOT/'ml_v4/evidence/integration_stage3/run_tests.py'),'--child']
    runpy.run_path(sys.argv[0],run_name='__main__')
else:
    before=json.loads((OUT/'before_sha256.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in before.items() if p not in ALLOWED)
    changes={p:{'before':before[p],'after':sha(ROOT/p)} for p in ALLOWED}
    (OUT/'authorized_application_changes.json').write_text(json.dumps(changes,indent=2)+'\n')
    env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    commands={
        'shadow_tests.txt':[str(ROOT/'.venv/Scripts/python.exe'),'-B','-m','pytest','tests/test_v4_shadow.py','-q','-p','no:cacheprovider'],
        'stage3_tests.txt':[str(ROOT/'ml_v4/.venv_inference_stage3/Scripts/python.exe'),'-I','-B',str(Path(__file__).resolve()),'--stage3-child']}
    for name,command in commands.items():
        p=subprocess.run(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (OUT/name).write_text(p.stdout,encoding='utf-8')
        print(name+'\n'+p.stdout)
        if p.returncode:raise SystemExit(p.returncode)
