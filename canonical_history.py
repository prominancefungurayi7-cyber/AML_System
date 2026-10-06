"""Controlled prototype coverage verification, not operator history or inference.

All public inputs are server-obtained snapshot records. No browser endpoint exists.
Attestations are scoped snapshots, never a permanent permission to use later rows.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json

from canonical_mobile_money import VERSION, FIELDS, LEGACY_TYPES, event_from_dict, utc_timestamp

SCOPE_VERSION = 'prototype.observation.v1'
SOURCE = 'application.transactions+canonical_mobile_money_events'
STATUSES = ('UNKNOWN', 'INCOMPLETE', 'COMPLETE_VERIFIED', 'TRUE_COLD_START_VERIFIED')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')


def boundary(scope_id, start, fence, authority, evidence):
    if not all(type(x) is str and x.strip() for x in (scope_id,authority,evidence)):
        raise ValueError('Server authority and evidence reference required')
    if type(fence) is not int or fence < 0:
        raise ValueError('Invalid transaction fence')
    return dict(scope_id=scope_id,scope_version=SCOPE_VERSION,revision=1,
        start_timestamp=utc_timestamp(start),start_transaction_id_exclusive=fence,
        source_ledger=SOURCE,canonical_version=VERSION,verification_timestamp=now(),
        verification_authority=authority,evidence_reference=evidence,status='UNKNOWN',
        claim='Controlled canonical prototype ledger only; no real operator or pre-boundary history claim')


def validate_scope(scope):
    if (scope['scope_version'] != SCOPE_VERSION or scope['source_ledger'] != SOURCE or
        scope['canonical_version'] != VERSION or scope['status'] != 'UNKNOWN' or
        type(scope['revision']) is not int or scope['revision'] < 1 or
        type(scope['start_transaction_id_exclusive']) is not int or scope['start_transaction_id_exclusive'] < 0 or
        utc_timestamp(scope['start_timestamp']) != scope['start_timestamp']):
        raise ValueError('Scope mismatch')


def verify(scope, parents, canonical, verified_at, previous=None, resolutions=None, changes=()):
    """Pure deterministic check. Parent/canonical lists must be ID ordered, complete.

    parents expose only immutable source identity, time, type, currency and agent;
    no historical float is used to create canonical cents. Canonical rows include
    Stage2's version and UNKNOWN marker. Missing counterparts block entire graph.
    """
    validate_scope(scope)
    verified_at=utc_timestamp(verified_at)
    resolutions=resolutions or {}
    issues=[]
    def issue(code, tx=None):
        issues.append({'code':code,'transaction_id':tx})
    if verified_at < scope['start_timestamp']:
        issue('VERIFICATION_BEFORE_BOUNDARY')
    for label, rows, field in (('PARENT',parents,'id'),('CANONICAL',canonical,'transaction_id')):
        ids=[r[field] for r in rows]
        if len(set(ids)) != len(ids): issue(label+'_DUPLICATE_ID')
        if ids != sorted(ids): issue(label+'_ORDER')
    pmap={r['id']:r for r in parents}
    cmap={r['transaction_id']:r for r in canonical}
    selected={}
    for p in parents:
        try:
            time=utc_timestamp(p['timestamp'])
        except (ValueError,TypeError):
            time=None
        # ID fence catches newly inserted backdated/ambiguous records; timestamp
        # catches future-dated pre-existing records. Neither is silently ignored.
        if (p['id'] > scope['start_transaction_id_exclusive'] or
            ('preexisting_parent_ids' in scope and p['id'] not in scope['preexisting_parent_ids']) or
            (time and time >= scope['start_timestamp'])):
            selected[p['id']]=(p,time)
    journal_ids=[r['change_id'] for r in changes]
    if len(set(journal_ids))!=len(journal_ids) or journal_ids!=sorted(journal_ids):issue('JOURNAL_ORDER_OR_DUPLICATE')
    journal_fingerprint={str(r['change_id']):digest(r) for r in changes}
    if previous:
        for key,value in previous.get('journal_fingerprint',{}).items():
            if journal_fingerprint.get(key)!=value:issue('JOURNAL_REVISION_OR_DELETION')
    for change in changes:
        if change['change_id'] in scope.get('preexisting_change_ids',[]):continue
        tx=change['transaction_id']
        relevant=(tx in selected or tx>scope['start_transaction_id_exclusive'] or
                  ('preexisting_parent_ids' in scope and tx not in scope['preexisting_parent_ids']))
        if relevant and change['operation'] in ('SOURCE_UPDATE','SOURCE_DELETE','CANONICAL_UPDATE','CANONICAL_DELETE'):
            issue('JOURNALED_MUTATION_'+change['operation'],tx)
        if relevant and change['operation']=='SOURCE_INSERT' and tx not in pmap:
            issue('JOURNALED_SOURCE_MISSING',tx)
    for c in canonical:
        if c['transaction_id'] not in pmap:
            issue('ORPHAN_CANONICAL',c['transaction_id'])
    fingerprint={}
    events=[]
    last=None
    for tx,(p,time) in selected.items():
        c=cmap.get(tx)
        fingerprint[str(tx)]={'parent':digest(p),'canonical':digest(c) if c else None}
        if time is None: issue('AMBIGUOUS_TIME',tx)
        elif time < scope['start_timestamp']: issue('BACKDATED_BEFORE_BOUNDARY',tx)
        elif time > verified_at: issue('FUTURE_EVENT',tx)
        if c is None:
            issue('MISSING_CANONICAL_COUNTERPART',tx)
            continue
        try:
            if set(c) != set(FIELDS)|{'canonical_version','history_status'}:
                raise ValueError('Unexpected schema')
            if c['canonical_version'] != VERSION or c['history_status'] != 'UNKNOWN':
                raise ValueError('Unsupported contract/source marker')
            e=event_from_dict({k:c[k] for k in FIELDS})
            if (p['sender_account'] != e.sender_wallet or p['receiver_account'] != e.receiver_wallet or
                p['transaction_type'] != LEGACY_TYPES[e.transaction_type] or p['currency'] != e.currency or
                str(p['agent_id'] or '') != e.agent_id or time != e.event_timestamp):
                raise ValueError('Parent identity/role mismatch')
            if last is not None and e.key <= last:
                issue('NONINCREASING_CAPTURE_KEY',tx)
            last=e.key
            events.append(e)
        except (ValueError,TypeError,KeyError):
            issue('UNSUPPORTED_OR_MISMATCHED_EVENT',tx)
    protected=dict(previous.get('protected_fingerprint',previous['fingerprint'])) if previous else {}
    if previous:
        if previous['scope_id'] != scope['scope_id'] or previous['boundary_digest'] != digest({k:scope[k] for k in ('scope_id','scope_version','start_timestamp','start_transaction_id_exclusive','source_ledger','canonical_version')}):
            issue('SCOPE_BOUNDARY_CHANGED')
        for tx,old in protected.items():
            current=fingerprint.get(tx)
            if current is None or old['parent'] != current['parent']:
                issue('DELETION_OR_SOURCE_REVISION',int(tx))
            elif old['canonical'] and old['canonical'] != current['canonical']:
                issue('CANONICAL_REVISION',int(tx))
            elif old['canonical'] is None and current['canonical'] is not None:
                if not isinstance(resolutions.get(tx),str) or not resolutions[tx].strip():
                    issue('RESOLUTION_EVIDENCE_REQUIRED',int(tx))
                else:
                    protected[tx]=current
    for tx,entry in fingerprint.items():
        protected.setdefault(tx,entry)
    # Global completeness is intentionally stronger than per-wallet checks.
    # Any gap could hide a graph edge connecting otherwise clean wallets.
    status='INCOMPLETE' if issues else 'COMPLETE_VERIFIED'
    through=[events[-1].event_timestamp,events[-1].transaction_id] if events else None
    observed_through=through
    if issues:through=None
    entities={}
    for e in events:
        keys=[('wallet',w) for w in sorted({e.sender_wallet,e.receiver_wallet})]
        if e.agent_id: keys.append(('agent',e.agent_id))
        for kind,identity in keys:
            key=kind+':'+identity
            state=entities.setdefault(key,dict(kind=kind,identity=identity,first_key=[e.event_timestamp,e.transaction_id],observations=0))
            state['observations']+=1
    for state in entities.values():
        state.update(status='INCOMPLETE' if issues else ('TRUE_COLD_START_VERIFIED' if state['observations']==1 else 'COMPLETE_VERIFIED'),
            complete_through_key=through,complete_through_timestamp=None if issues else verified_at,
            scope_id=scope['scope_id'],scope_version=SCOPE_VERSION,canonical_version=VERSION,scope_revision=scope['revision'])
    b={k:scope[k] for k in ('scope_id','scope_version','start_timestamp','start_transaction_id_exclusive','source_ledger','canonical_version')}
    protected_journal=dict(previous.get('journal_fingerprint',{})) if previous else {}
    for key,value in journal_fingerprint.items():protected_journal.setdefault(key,value)
    return dict(scope_id=scope['scope_id'],scope_version=SCOPE_VERSION,scope_revision=scope['revision'],
        boundary_digest=digest(b),status=status,verified_at=verified_at,complete_through_key=through,
        complete_through_timestamp=None if issues else verified_at,observed_through_key=observed_through,source_revision=digest(fingerprint),fingerprint=fingerprint,protected_fingerprint=protected,
        journal_fingerprint=protected_journal,
        issues=issues,entities=entities,canonical_event_ids=[e.transaction_id for e in events],
        resolution_references=resolutions,graph_scope='All post-boundary prototype transactions, no entity or edge filters')


def freshness(scope, current, attested):
    if current['status']=='INCOMPLETE': return 'INCOMPLETE'
    if not attested or attested['scope_revision']!=scope['revision'] or attested['source_revision']!=current['source_revision'] or attested['boundary_digest']!=current['boundary_digest']:
        return 'UNKNOWN'
    return attested['status']


def window_coverage(scope, at):
    """Full-window maturity only; younger known scope may still be valid cold start."""
    end=datetime.fromisoformat(utc_timestamp(at).replace('Z','+00:00'))
    start=datetime.fromisoformat(scope['start_timestamp'].replace('Z','+00:00'))
    hours={'1h':1,'24h':24,'7d':168,'28d':672,'28d1h':673,'29d':696,'35d':840}
    out={name:start<=end-timedelta(hours=n) for name,n in hours.items()}
    out['prior28_utc_days']=start<=end.replace(hour=0,minute=0,second=0,microsecond=0)-timedelta(days=28)
    return out
