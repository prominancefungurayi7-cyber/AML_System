"""Recover only exact manifest bytes from local files or recorded textual patches.

Never executes session commands. Patches are parsed as data into memory; only
content matching the historical SHA-256 may be restored to a missing path.
"""
import hashlib,json,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
LOG=Path(r'C:\Users\PROMINENT\.codex\sessions\2026\10\03\rollout-2026-10-03T19-56-10-01a0c658-9330-7983-830e-9c584a204637_01a102e8-c1e8-7252-bb32-aa6c70e7e7d7.jsonl')
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
manifest=json.loads((ROOT/'ml_v4/evidence/integration_stage3/decision.json').read_text())
expected=manifest['artifact_sha256']
missing={p:h for p,h in expected.items() if not (ROOT/p).is_file()}
assert len(missing)==12
present={p:sha((ROOT/p).read_bytes()) for p in expected if (ROOT/p).is_file()}
assert all(expected[p]==h for p,h in present.items())
save('missing_files.json',missing)
found={};searched=[];states={};errors=[]
names={Path(p).name for p in missing}
excluded={'.git','.venv','node_modules','__pycache__','models','artifacts','matrices','data','datasets','generation','sealed','final_test','independent_evaluation','.venv_inference_stage3'}
roots=[ROOT,ROOT.parent,Path(r'C:\Users\PROMINENT\.codex\tmp'),Path(r'C:\Users\PROMINENT\.codex\.tmp'),Path(os.environ.get('TEMP','C:/Temp'))]
seen=set()
for base in roots:
    if not base.is_dir():continue
    searched.append(str(base))
    for folder,dirs,files in os.walk(base):
        dirs[:]=[d for d in dirs if d.lower() not in excluded and not any(t in d.lower() for t in ('sealed','evaluation','final_test'))]
        for name in files:
            if name not in names:continue
            p=Path(folder)/name
            if str(p) in seen:continue
            seen.add(str(p))
            try:
                if p.stat().st_size>2000000:continue
                data=p.read_bytes();h=sha(data)
            except OSError:continue
            for target,want in missing.items():
                if h==want:found[target]=(data,{'method':'exact file copy','source':str(p)})
save('copy_search.json',{'roots':searched,'candidate_filenames_examined':len(seen),'exact_file_matches':list(found),'exclusions':sorted(excluded),'archive_contents_not_expanded':True})

def check(path,lines,origin):
    for newline in ('\n','\r\n'):
        data=(newline.join(lines)+newline).encode('utf-8')
        if sha(data)==missing[path]:found[path]=(data,{**origin,'line_endings':'LF' if newline=='\n' else 'CRLF','method':'exact bytes reproduced from retained original patch records'})

pattern=re.compile(r'tools\.apply_patch\(("(?:[^"\\]|\\.)*")\)')
for number,line in enumerate(LOG.open(encoding='utf-8'),1):
    obj=json.loads(line);payload=obj.get('payload',{})
    if obj.get('type')!='response_item' or payload.get('type')!='custom_tool_call' or payload.get('name')!='exec':continue
    for match in pattern.finditer(payload.get('input','')):
        patch=json.loads(match.group(1));lines=patch.splitlines();i=0
        while i<len(lines):
            head=lines[i];i+=1
            if not head.startswith(('*** Add File: ','*** Update File: ','*** Delete File: ')):continue
            kind,path=head[4:].split(' File: ',1)
            block=[]
            while i<len(lines) and not lines[i].startswith('*** '):block.append(lines[i]);i+=1
            if path not in missing:continue
            origin={'source':str(LOG),'record_line':number,'call_id':payload.get('call_id'),'operation':kind}
            if kind=='Add':states[path]=[x[1:] for x in block if x.startswith('+')]
            elif kind=='Delete':continue
            elif path in states:
                hunks=[];hunk=[]
                for x in block:
                    if x.startswith('@@'):
                        if hunk:hunks.append(hunk)
                        hunk=[]
                    else:hunk.append(x)
                if hunk:hunks.append(hunk)
                candidate=list(states[path]);ok=True
                for hunk in hunks:
                    old=[x[1:] for x in hunk if x.startswith((' ','-'))]
                    new=[x[1:] for x in hunk if x.startswith((' ','+'))]
                    positions=[k for k in range(len(candidate)-len(old)+1) if candidate[k:k+len(old)]==old]
                    if len(positions)!=1:ok=False;break
                    k=positions[0];candidate[k:k+len(old)]=new
                if not ok:
                    errors.append({'path':path,'record_line':number,'reason':'patch context not unique/applicable; not executed'})
                    continue
                states[path]=candidate
            if path in states:check(path,states[path],origin)
records=[]
for p,(data,origin) in found.items():
    assert sha(data)==missing[p]
    dest=ROOT/p
    assert not dest.exists(), 'Never overwrite an existing destination'
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(data)
    records.append(dict(destination=p,expected_sha256=missing[p],actual_sha256=sha(dest.read_bytes()),**origin))
save('recovery_records.json',{'records':records,'unrecovered':[p for p in missing if p not in found],
    'session_commands_executed':False,'patch_context_skips':errors,'historical_manifest_changed':False})
print(json.dumps({'missing':len(missing),'exact_restored':len(records),'unrecovered':[p for p in missing if p not in found]}))
