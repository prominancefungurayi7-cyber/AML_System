"""Offline isolated runtime from exact installed research distributions."""
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import shutil
import sys
import venv

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
prior=ROOT/'ml_v4/evidence/integration_stage2a2'
expected=json.loads((prior/'before_sha256.json').read_text())
expected.update(json.loads((prior/'decision.json').read_text(encoding='utf-8'))['artifact_sha256'])
expected['ml_v4/evidence/integration_stage2a2/decision.json']=sha(prior/'decision.json')
assert all(sha(ROOT/p)==h for p,h in expected.items())
(OUT/'before_sha256.json').write_text(json.dumps(expected,indent=2)+'\n')
freeze=ROOT/'ml_v4/evidence/stage23/development_candidate_freeze.json'
f=json.loads(freeze.read_text())
service=ROOT/'ml_v4/frozen_inference'
service.mkdir(exist_ok=True)
authority={k:v for k,v in f['artifacts'].items() if k in ('pipeline','extractor_source','feature_specification','observable_contract_source','preprocessor_source','preprocessing_specification','standalone_fitted_preprocessor')}
authority['freeze']={'path':str(freeze.relative_to(ROOT)).replace('\\','/'),'sha256':sha(freeze)}
(service/'authority.json').write_text(json.dumps({'freeze_id':f['freeze_id'],'feature_version':'v4.features.1','artifacts':authority,'runtime':f['runtime']['freeze_runtime_package_pins'],'python':'3.14.3','configuration':f['configuration']},indent=2)+'\n')
env=ROOT/'ml_v4/.venv_inference_stage3'
assert not env.exists(), 'Do not overwrite environment'
venv.EnvBuilder(with_pip=False,system_site_packages=False).create(env)
target=env/'Lib/site-packages'
records={}
packages=list(f['runtime']['freeze_runtime_package_pins'])+['pytest','pluggy','packaging','iniconfig','pygments','colorama']
for name in packages:
    dist=md.distribution(name)
    if name in f['runtime']['freeze_runtime_package_pins']:
        assert dist.version==f['runtime']['freeze_runtime_package_pins'][name]
    files={}
    base=Path(dist.locate_file('')).resolve()
    for entry in dist.files:
        source=Path(dist.locate_file(entry)).resolve()
        if not source.is_relative_to(base) or not source.is_file() or source.suffix=='.pyc': continue
        relative=source.relative_to(base)
        dest=target/relative
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,dest)
        assert sha(source)==sha(dest)
        files[str(relative).replace('\\','/')]=sha(dest)
    records[name]={'version':dist.version,'files':files}
(OUT/'runtime_files.json').write_text(json.dumps(records,indent=2)+'\n')
(OUT/'runtime_preparation.json').write_text(json.dumps({'python':sys.version,'base_interpreter_sha256':sha(Path(sys.executable)),'isolated_prefix':str(env),'system_site_packages':False,'method':'Offline exact distribution-file copies, hashed source and destination; not original wheel lock','application_environment_modified':False,'packages':{k:v['version'] for k,v in records.items()}},indent=2)+'\n')
print(json.dumps({'protected':len(expected),'runtime':str(env),'packages':len(records)}))
