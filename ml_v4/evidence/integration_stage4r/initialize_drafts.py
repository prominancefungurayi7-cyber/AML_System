"""Retrieve our prior unexecuted integration drafts as new Stage4R work."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
log=Path(r'C:\Users\PROMINENT\.codex\sessions\2026\10\03\rollout-2026-10-03T19-56-10-01a0c658-9330-7983-830e-9c584a204637_01a102e8-c1e8-7252-bb32-aa6c70e7e7d7.jsonl')
targets=['v4_shadow.py','ml_v4/shadow_integration/worker.py']
found={}
for line in log.open(encoding='utf-8'):
    q=json.loads(line).get('payload',{})
    if q.get('type')!='custom_tool_call':continue
    for m in re.finditer(r'tools\.apply_patch\(("(?:[^"\\]|\\.)*")\)',q.get('input','')):
        patch=json.loads(m.group(1))
        for target in targets:
            start='*** Add File: '+target+'\n'
            if start in patch:
                block=patch.split(start,1)[1].split('*** ',1)[0]
                found[target]='\n'.join(x[1:] for x in block.splitlines() if x.startswith('+'))+'\n'
for target in targets:
    p=ROOT/target
    assert not p.exists()
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(found[target],encoding='utf-8')
print('New Stage4R drafts initialized; not executed.')
