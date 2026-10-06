"""Trusted complete-snapshot gate. Never accepts caller-asserted completeness."""
import json
from pathlib import Path
from .service import ROOT,Failure,verified_bytes

SCOPE='controlled-prototype-v1'

def verified_snapshot(c,tx):
    pins=json.loads((Path(__file__).parent/'history_authority.json').read_text())
    for path,h in pins.items(): verified_bytes({'path':path,'sha256':h})
    from canonical_history_store import assess,snapshot
    from canonical_history import freshness
    from canonical_history_journal import triggers,ensure
    from canonical_mobile_money import FIELDS
    try:
        if c.engine not in ('mysql','sqlite'): raise Failure('HISTORY_INCOMPLETE')
        if c.engine=='mysql':
            c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            c.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
            if c.execute('SELECT DATABASE() AS db').fetchone()['db']!='aml': raise Failure('HISTORY_INCOMPLETE')
            rows=c.execute("SELECT TRIGGER_NAME,EVENT_OBJECT_TABLE,EVENT_MANIPULATION,ACTION_TIMING,ACTION_STATEMENT FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()").fetchall()
            rows=[r for r in rows if r['TRIGGER_NAME'].lower().startswith('cmm_')]
            want=triggers('mysql')
            if {r['TRIGGER_NAME'] for r in rows}!=set(want): raise Failure('HISTORY_INCOMPLETE')
            for r in rows:
                table,op,body=want[r['TRIGGER_NAME']]
                if (r['EVENT_OBJECT_TABLE'],r['EVENT_MANIPULATION'],r['ACTION_TIMING'],r['ACTION_STATEMENT'])!=(table,op,'AFTER',body): raise Failure('HISTORY_INCOMPLETE')
        else:
            # SQLite is a hand-fixture adapter only, never a live application alternative.
            if c.execute('PRAGMA database_list').fetchone()['file']: raise Failure('HISTORY_INCOMPLETE')
            c.execute('BEGIN')
        ensure(c)
        scope,current,previous=assess(c,SCOPE)
        if c.engine=='mysql':
            original=json.loads((ROOT/'ml_v4/evidence/integration_stage2a2/observation_boundary.json').read_text())
            keys=('scope_id','scope_version','start_timestamp','start_transaction_id_exclusive','source_ledger','canonical_version','preexisting_parent_ids','preexisting_change_ids')
            if any(scope[k]!=original[k] for k in keys): raise Failure('HISTORY_INCOMPLETE')
        actual=freshness(scope,current,previous)
        if actual!='COMPLETE_VERIFIED' or current['issues'] or scope['scope_version']!='prototype.observation.v1': raise Failure('HISTORY_INCOMPLETE')
        if current['graph_scope']!='All post-boundary prototype transactions, no entity or edge filters': raise Failure('HISTORY_INCOMPLETE')
        parents,canonical,changes=snapshot(c)
        allowed=set(current['canonical_event_ids'])
        if tx not in allowed: raise Failure('EVENT_UNAVAILABLE')
        events=[{k:r[k] for k in FIELDS} for r in canonical if r['transaction_id'] in allowed]
        if len(events)!=len(allowed): raise Failure('HISTORY_INCOMPLETE')
        # Full scoped graph is returned; request-local replay stops at the decision key.
        chosen=next(e for e in events if e['transaction_id']==tx)
        context=dict(event_timestamp=chosen['event_timestamp'],observation_scope=scope['scope_id'],
            scope_revision=scope['revision'],source_revision=current['source_revision'],history_status=actual,
            history_complete_through=dict(key=current['complete_through_key'],timestamp=current['complete_through_timestamp']),
            history_scope_warning='Controlled canonical prototype ledger from observation boundary only; no pre-boundary or operator completeness claim.')
        return events,context
    except Failure: raise
    except MemoryError: raise Failure('HISTORY_RESOURCE_EXHAUSTED') from None
    except Exception: raise Failure('HISTORY_INCOMPLETE') from None
