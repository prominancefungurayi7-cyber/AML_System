"""Read-only local verification and administrator handoff; no DB connection."""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT = ROOT / 'ml_v4/reports/V4_INTEGRATION_STAGE2A1_CAPTURE_ACTIVATION_REPORT.md'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

prior = ROOT / 'ml_v4/evidence/integration_stage2a'
decision = json.loads((prior / 'decision.json').read_text(encoding='utf-8'))
expected = json.loads((prior / 'before_sha256.json').read_text(encoding='utf-8'))
expected.update(decision['artifact_sha256'])
expected['ml_v4/evidence/integration_stage2a/decision.json'] = sha(prior / 'decision.json')
actual = {name: sha(ROOT / name) for name in expected}
assert actual == expected, 'Protected file mismatch; stop'
save('before_sha256.json', actual)

spec = importlib.util.spec_from_file_location('verified_journal', ROOT / 'canonical_history_journal.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sql_path = prior / 'admin_capture_triggers.sql'
sql = sql_path.read_text(encoding='utf-8')
statements = [line for line in sql.splitlines() if line.startswith('CREATE TRIGGER ')]
wanted = [f'CREATE TRIGGER {name} AFTER {op} ON {table} FOR EACH ROW {body}$$'
          for name, (table, op, body) in module.triggers('mysql').items()]
assert statements == wanted and len(statements) == 6
save('trigger_verification.json', {
    'reviewed_sql_sha256': sha(sql_path), 'stage2a_hash_match': True,
    'exact_six_statements_match_verified_stage2a_source': True,
    'expected': {name: {'table': table, 'timing': 'AFTER', 'event': op,
                         'body_sha256': hashlib.sha256(body.encode()).hexdigest()}
                 for name, (table, op, body) in module.triggers('mysql').items()},
    'live_metadata_verification': 'NOT_RUN: administrator identity unavailable',
    'last_stage2a_installed_triggers': [], 'current_installation_status': 'NOT_REVERIFIED'
})
save('activation_status.json', {
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'decision': 'C', 'privilege_method_used': 'NONE',
    'credential_discovery_scope': 'Nonempty configuration key names in process environment and workspace .env only; values not exported',
    'database_configuration_keys': ['DATABASE_URL'],
    'authorized_admin_identity_available': False,
    'prior_blocker': 'Stage2A MySQL error 1419; no triggers installed in recorded postconditions',
    'database_connection_this_stage': False,
    'installation': 'NOT_RUN', 'mysql_capture_test': 'NOT_RUN',
    'rollback_test': 'NOT_RUN', 'migration_idempotency': 'NOT_RUN',
    'observation_boundary': 'NOT_CREATED', 'first_attestation': 'NOT_RUN',
    'freshness_source_revision_watermark_entities_graph': 'NOT_VERIFIED',
    'history_status': 'UNKNOWN; no new completeness claim',
    'database_mutations': 0, 'model_operations': 0
})
REPORT.write_text('''# MODEL V4 — INTEGRATION STAGE 2A.1 MYSQL CAPTURE ACTIVATION AND HISTORY BOUNDARY VERIFICATION

**C — AUTHORIZED MYSQL ADMINISTRATOR ACTION STILL REQUIRED**

## 1. Decision and privilege boundary

No already-authorized MySQL administrator/migration identity was supplied or configured in the checked connection configuration. Only the existing application `DATABASE_URL` is present. Discovery checked nonempty key names in the process environment and workspace `.env`; credentials were not exported, and no credential stores or guessed accounts were tried. This is a bounded availability check, not a claim that no administrator exists elsewhere.

Stage2A recorded MySQL error **1419**, no installed capture triggers, four empty history-state tables and no observation scope. Those are verified historical evidence, not fresh database observations. In accordance with the explicit Stage2A.1 stop rule, this stage opened no database connection and attempted no installation. Privilege method used: **none**. No binary-log setting, trust setting or account privilege was changed.

## 2. Reviewed definitions verified

The existing [administrator SQL](../evidence/integration_stage2a/admin_capture_triggers.sql) matches the Stage2A manifest SHA-256:

`6a39ddc6c5663573ff2203c47997929dbc1f785851cd26361770cf40a12ed310`

All six complete CREATE statements match the hash-verified `canonical_history_journal.py` definitions exactly, including AFTER timing, table, event and body. Required names are `cmm_tx_insert`, `cmm_tx_update`, `cmm_tx_delete`, `cmm_ce_insert`, `cmm_ce_update`, `cmm_ce_delete`. Parent UPDATE captures changes to id, time, endpoints, type, currency, agent and amount; operational-only risk/description changes are excluded. No trigger logic was rewritten. [Verification evidence](../evidence/integration_stage2a1/trigger_verification.json).

## 3. Exact administrator handoff

An administrator must open the MySQL client using an **existing authorized migration identity**, select the same host, port and schema as the application DATABASE_URL, and enter the password interactively. Replace the angle-bracket placeholders with those actual connection values; do not use the application identity or put a password in a command argument.

```text
mysql --host=<application-host> --port=<application-port> --user=<authorized-migration-user> --password --database=<application-schema>
```

In that authenticated MySQL session, after confirming the target schema and that no conflicting CMM trigger already exists, execute this exact command:

```sql
SOURCE C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v4/evidence/integration_stage2a/admin_capture_triggers.sql;
```

The SQL is not an idempotent installer: if any trigger already exists, inspect its definition first; do not blindly rerun, drop or replace it. Retain any partial-installation evidence. Installation must not change business rows. Do not disable binary logging, enable `log_bin_trust_function_creators`, or grant SUPER/broad privileges to the application account.

After installation, capture MySQL metadata and verify all six names, exact tables, AFTER timing, INSERT/UPDATE/DELETE events and exact bodies, and reject unexpected CMM triggers. Only then run the authorized disposable MySQL capture tests. Installation alone does not authorize a completeness claim or a retroactive boundary.

## 4. Execution gates and remaining work

| Gate | This stage |
| --- | --- |
| Local SQL hash and six definition comparisons | PASS |
| Live trigger installation / metadata / unexpected-trigger check | NOT RUN — administrator identity unavailable |
| Parent and canonical INSERT/UPDATE/DELETE capture | NOT RUN |
| Rollback leaves no committed journal; operational-only UPDATE exclusion | NOT RUN |
| Deterministic journal order; repeated migration/inspection idempotency | NOT RUN |
| Disposable fixture cleanup | NOT APPLICABLE — no fixture created |
| First actual post-capture observation boundary | NOT CREATED |
| First computed attestation / freshness / revision / watermark | NOT RUN |
| Entity state and global graph scope verification | NOT RUN |

The existing Stage2A implementation remains authoritative. Resume with a documented administrator installation and the disposable MySQL tests. After all capture gates pass, establish the first actual post-capture boundary with UTC start, transaction fence, visible membership, source, canonical version, revision, evidence and verification identity. Begin at UNKNOWN and let the existing attestation calculate the result; never request or override a desired status. Global graph completeness and entity cold-start claims retain their scoped prototype meaning. No interval before capture activation is certified.

History status remains **UNKNOWN / unavailable for a new completeness claim**. The current database state was not rechecked. Stage2A SQLite tests are historical evidence and are not substituted for the required MySQL tests. [Execution status](../evidence/integration_stage2a1/activation_status.json).

## 5. Preservation and limitations

All PROTECTED_COUNT named protected files match their inherited expected hashes before and after this stage, including Stage2A implementation/evidence and inherited V1/V3/V4 references. The Stage2A decision itself is additionally protected against changes during this stage. [Preservation evidence](../evidence/integration_stage2a1/preservation_verification.json).

No application code, database schema, row, scope or attestation was changed by this work. No ambiguous row was converted, disposable or synthetic history created, model loaded/deserialized, feature calculated, prediction made, fit performed or threshold changed. Sealed files were not accessed. Because no database connection was opened, this stage makes no fresh recordset-equality claim about unrelated concurrent activity. Earlier custody and historical archive limitations remain unresolved. Writes are confined to this report and the Stage2A.1 evidence directory; the [decision manifest](../evidence/integration_stage2a1/decision.json) binds them.

## 6. Final decision

**C — AUTHORIZED MYSQL ADMINISTRATOR ACTION STILL REQUIRED**

The reviewed SQL is intact and ready for the administrator handoff. Capture activation and all dependent history-verification gates remain pending. Integration Stage3 has not begun.

V4 INTEGRATION STAGE 2A.1 COMPLETE —
WAITING FOR APPROVAL.
'''.replace('PROTECTED_COUNT', str(len(expected))), encoding='utf-8')
after = {name: sha(ROOT / name) for name in expected}
assert after == actual
save('preservation_verification.json', {'protected_count': len(expected), 'all_match': True,
    'after_sha256': after, 'database_access': False,
    'database_row_preservation': 'No writes by this stage; concurrent external changes not verified'})
outputs = list(OUT.glob('*')) + [REPORT]
save('decision.json', {'decision': 'C — AUTHORIZED MYSQL ADMINISTRATOR ACTION STILL REQUIRED',
    'protected_count': len(expected), 'installation_attempted': False,
    'artifact_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p)
                       for p in outputs if p.is_file() and p.name != 'decision.json'}})
print(json.dumps({'decision': 'C', 'protected_count': len(expected), 'definitions_verified': 6}))
