"""Copy named already-installed supporting dependencies to isolated runtime."""
import hashlib,importlib.metadata as md,json,shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
target=root/'ml_v4/.venv_inference_stage3/Lib/site-packages'
records={}
for name in sys.argv[1:]:
    dist=md.distribution(name);base=Path(dist.locate_file('')).resolve();files={}
    for entry in dist.files:
        src=Path(dist.locate_file(entry)).resolve()
        if not src.is_relative_to(base) or not src.is_file() or src.suffix=='.pyc':continue
        rel=src.relative_to(base);dest=target/rel
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
        h=hashlib.sha256(src.read_bytes()).hexdigest()
        assert hashlib.sha256(dest.read_bytes()).hexdigest()==h
        files[str(rel).replace('\\','/')]=h
    records[name]={'version':dist.version,'files':files}
out=Path(__file__).parent/('supporting_'+sys.argv[1]+'.json')
assert not out.exists()
out.write_text(json.dumps(records,indent=2)+'\n')
print({n:v['version'] for n,v in records.items()})
