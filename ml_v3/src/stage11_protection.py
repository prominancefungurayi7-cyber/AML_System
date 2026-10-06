"""Stage 11 explicit protection scope; never list evaluation roots."""
from stage10a_protection import ROOT, sha, snapshot as prior_snapshot, compare

def snapshot():
    result=prior_snapshot()
    roots=('ml_v2/redesign','ml_v2/models','ml_v3/features/development/stage10a')
    for rel in roots:
        folder=ROOT.parent/rel
        if folder.exists():
            for p in folder.rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts:
                    result['files'][p.relative_to(ROOT.parent).as_posix()]=sha(p)
    for pattern in ('*STAGE10A*','stage10a_*.json'):
        for p in (ROOT/'reports').glob(pattern):
            if p.is_file(): result['files'][p.relative_to(ROOT.parent).as_posix()]=sha(p)
    for pattern in ('*stage10a*.py',):
        for folder in ('src','tests'):
            for p in (ROOT/folder).glob(pattern): result['files'][p.relative_to(ROOT.parent).as_posix()]=sha(p)
    result['scope']+=list(roots)+['ml_v3/reports/*STAGE10A* and stage10a_*.json','ml_v3/src and tests: *stage10a*.py']
    return result
