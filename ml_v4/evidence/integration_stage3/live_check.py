"""Read-only history inspection; intentionally no actual-event model call."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from ml_v4.frozen_inference.cli import connection
from ml_v4.frozen_inference.history import verified_snapshot
from ml_v4.frozen_inference.service import Failure
from canonical_history_store import assess
from canonical_history import freshness

out={}
c=connection()
try:
    # Positive integer sentinel is queried only, never inserted. Gate checks live
    # triggers, frozen boundary and attestation before reporting no such event.
    try:
        verified_snapshot(c,2**63-1)
        raise AssertionError('Unexpected sentinel transaction')
    except Failure as exc:
        out['gate_result']=exc.code
        assert exc.code=='EVENT_UNAVAILABLE'
    s,a,previous=assess(c,'controlled-prototype-v1')
    out.update(history_status=freshness(s,a,previous),scope_revision=s['revision'],
        scope_version=s['scope_version'],scope_start=s['start_timestamp'],source_revision=a['source_revision'],
        canonical_event_count=len(a['canonical_event_ids']),entity_count=len(a['entities']),
        complete_through_key=a['complete_through_key'],attestation_timestamp=previous['verified_at'],
        graph_scope=a['graph_scope'],checked_at=a['verified_at'],issues=a['issues'],
        database_writes=0,features_extracted=0,predictions=0)
finally:
    c.rollback();c.close()
path=Path(__file__).parent/'live_history_check.json'
assert not path.exists()
path.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
