"""TEST ONLY: controlled SQLite fixture copied to in-memory Stage3 adapter.

Not the production launcher; never reads MySQL or accepts web input.
"""
from pathlib import Path
import json,sqlite3,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from database import DatabaseAdapter
from canonical_history_store import attest
from ml_v4.frozen_inference.service import infer
source=sqlite3.connect('file:'+Path(sys.argv[1]).resolve().as_posix()+'?mode=ro',uri=True)
memory=sqlite3.connect(':memory:');source.backup(memory);source.close()
memory.row_factory=sqlite3.Row;c=DatabaseAdapter(memory,'sqlite')
result=attest(c,'controlled-prototype-v1','isolated-test-technical-verifier','stage4r-hand-fixture')
c.commit()
assert result['status']=='COMPLETE_VERIFIED'
assert all(e['status']=='TRUE_COLD_START_VERIFIED' for e in result['entities'].values())
print(json.dumps(infer(lambda:c,int(sys.argv[2])),allow_nan=False))
