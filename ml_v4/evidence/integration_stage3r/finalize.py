"""Recovery report and source-only backup; no historical output writes."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
records=read(OUT/'recovery_records.json')
missing=read(OUT/'missing_files.json')
assert len(records['records'])==12 and not records['unrecovered']
assert all(sha(ROOT/p)==h for p,h in missing.items())
stage3=ROOT/'ml_v4/evidence/integration_stage3'
expected=read(stage3/'before_sha256.json')
expected.update(read(stage3/'decision.json')['artifact_sha256'])
expected['ml_v4/evidence/integration_stage3/decision.json']=read(ROOT/'ml_v4/evidence/integration_stage4/preflight_integrity.json')['expected']['ml_v4/evidence/integration_stage3/decision.json']
stage4=ROOT/'ml_v4/evidence/integration_stage4'
expected.update(read(stage4/'decision.json')['artifact_sha256'])
stage4_decision_before=sha(stage4/'decision.json')
actual={p:sha(ROOT/p) for p in expected}
assert actual==expected
assert '54 passed' in (OUT/'test_results.txt').read_text()
parity=read(OUT/'parity.json')
assert parity==read(stage3/'parity.json')
assert sum(len(p['indices']) for p in parity)==128
from ml_v4.frozen_inference.service import runtime
versions=runtime()
save('runtime_verification.json',{'versions':versions,'interpreter':sys.executable,'prefix':sys.prefix,'no_environment_modification':True})
archive=OUT/'approved_stage3_source_backup.zip'
assert not archive.exists()
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p,h in missing.items():z.writestr(p,(ROOT/p).read_bytes())
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())==set(missing)
    assert all(hashlib.sha256(z.read(p)).hexdigest()==h for p,h in missing.items())
save('source_backup_manifest.json',{'archive':archive.name,'sha256':sha(archive),'entries':missing,'model_data_credentials_runtime_included':False})
save('cause_assessment.json',{'conclusion':'CAUSE NOT ESTABLISHED',
    'git_evidence':'No tracked files or historical commits found for approved inference source during Stage4 checks',
    'session_check':'No recorded deletion-operation tool call naming one of the twelve exact missing paths found in the recovery session log',
    'limits':'Does not rule out generic cleanup, external tools, other sessions, workspace reset or unsaved automation. No such cause is asserted.',
    'prevention':'Exact source-only archive plus per-entry hashes created; recommend tracking recovered source and evidence scripts in Git, excluding binaries, datasets, credentials and runtime environments.'})
save('preservation_verification.json',{'all_named_expected_files_match':True,'named_count':len(expected),
    'exact_restorations':list(missing),'existing_named_files_unchanged':len(expected)-12,
    'hashes':actual,'stage4_decision_sha256':stage4_decision_before,
    'historical_stage3_parity_unchanged':sha(stage3/'parity.json'),
    'historical_stage3_test_output_unchanged':sha(stage3/'test_results.txt'),
    'fits':0,'database_connections':0,'stage4_resumed':False})
table='\n'.join('| `'+p+'` | `'+h+'` |' for p,h in missing.items())
report=ROOT/'ml_v4/reports/V4_INTEGRATION_STAGE3R_RECOVERY_REPORT.md'
report.write_text(f'''# MODEL V4 — INTEGRATION STAGE 3R APPROVED STAGE3 IMPLEMENTATION RECOVERY

**A — EXACT STAGE3 IMPLEMENTATION RECOVERED AND PARITY REVERIFIED**

**EXACT RECOVERY VERIFIED.** All twelve missing files have been restored with bytes matching their original historical Stage3 SHA-256 values. The original approved test workflow passed **54 tests** in the isolated runtime. All **128 fixed development examples** again produced maximum absolute probability difference **0**, with exact preprocessing parity. Stage4 was not resumed.

## A. Recovery authority and discovery

The missing list was recalculated directly from the historical Stage3 decision manifest: seven service/documentation/test files and five evidence scripts. Present Stage3 artifacts were checked before recovery. Neither the historical manifest nor its hashes, report or Decision A was changed.

Discovery searched the local project/parent project area, accessible Codex temporary directories and the system temporary directory for matching filenames and hashes. Runtime, model, dataset, matrix, generation and sealed/evaluation directories were excluded as recovery material. There were no exact standalone-file matches in the searched candidates. Git had no tracked/history copies for the approved service. Search scope and exclusions are in [copy search](../evidence/integration_stage3r/copy_search.json); archive contents and further editor stores were not exhaustively searched after the original command records yielded exact bytes.

The original source-generation and update patches were retained in a local Codex execution record. The recovery utility parsed only the recorded patch text as data, applied applicable textual hunks in memory, and checked candidate bytes against the historical expected hashes. It did **not execute any recorded command**. Each destination was created only after an exact SHA-256 match, using exclusive creation to prevent overwriting existing files. LF/CRLF selection was accepted only where it produced the original hash.

The recovery location is the local session record ending in `rollout-2026-10-03T19-56-10-01a0c658-9330-7983-830e-9c584a204637_01a102e8-c1e8-7252-bb32-aa6c70e7e7d7.jsonl`. Full source location, command call ID, record line, destination, newline form and expected/actual hashes are recorded per file in [recovery records](../evidence/integration_stage3r/recovery_records.json). Unrelated session content and credentials were not copied into evidence.

## B. Exact files and hashes

Every actual restored hash equals the value below from the untouched Stage3 manifest.

| Restored path | Expected = actual SHA-256 |
| --- | --- |
{table}

## C. Files not exactly recoverable

**None.** All twelve missing manifest-bound files were restored exactly. [Original missing-file record](../evidence/integration_stage3r/missing_files.json).

## D. Reconstructed implementation

**None.** No replacement design or `frozen_inference_recovered` identity was created. Reproducing the original recorded edits yielded the exact historical bytes; this is not a merely behaviorally equivalent reimplementation. The new recovery/validation/reporting utilities live only under `ml_v4/evidence/integration_stage3r/` and have their own manifest identity.

## E. Source gate and behavioral validation

All restored Stage3 artifact hashes and the frozen authority references were verified **before model deserialization**. The original Stage18 XGBoost remains at its authoritative path with SHA-256 `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. The original Stage17 extractor, feature specification, Event contract and embedded preprocessing identity match. [Pre-load source gate](../evidence/integration_stage3r/source_integrity_gate.json).

The restored original `run_tests.py --child` workflow executed the unchanged approved test suite. A validation harness redirected its generated parity evidence to Stage3R and captured fresh test output there. Historical Stage3 parity/test files were not overwritten. Environment-preparation and historical finalizer scripts were restored but not rerun, since they would recreate or rewrite historical outputs.

Results:

- **54 tests passed**; the original acceptance behavior was exercised without changing test source.
- Exactly40 semantic inputs and42 encoded columns; embedded preprocessing applied once.
-64 fixed Train plus64 fixed Validation examples, using the same retained indices; maximum probability difference0 and exact preprocessing equality.
- Class1 probability semantics, inclusive0.50 threshold, normal/error separation and no fallback.
- Fail-closed UNKNOWN/INCOMPLETE/stale history, graph completeness, same-time order, future invariance and cold-start behavior.
- Frozen N4 NaN and signed-marker handling, graph/funding/agent fixtures, resource errors and request-local concurrency.
- Two fresh processes reproduced identical fixture feature bytes and probability.
- Fit methods were guarded against execution; no training, calibration, threshold search or model selection occurred.

The new parity JSON equals the original retained parity JSON. These are development/fixture checks, not new effectiveness or generalization evidence. [Test results](../evidence/integration_stage3r/test_results.txt), [parity](../evidence/integration_stage3r/parity.json). No live database connection, live feature extraction or production prediction occurred in recovery; hand fixtures remained isolated.

## F. Runtime

The retained isolated environment `ml_v4/.venv_inference_stage3` passed the restored loader's runtime and origin checks: Python3.14.3, NumPy2.4.3, scikit-learn1.9.0, XGBoost3.4.1, SciPy1.18.0, joblib1.5.3 and threadpoolctl3.6.0. Native inference remains limited to one thread. No application/runtime package installation or environment change was needed. This does not add a historical wheel-provenance claim. [Runtime verification](../evidence/integration_stage3r/runtime_verification.json).

## G. Preservation

**{len(expected)} named expected artifacts match at completion**, comprising the exact restored files and {len(expected)-12} existing files unchanged against inherited expected hashes. The Stage4 decision was additionally hashed and preserved. Stage3's historical Decision A and Stage4's historical Decision C remain untouched. No previous evidence file was refreshed under its old identity.

Frozen model/preprocessing, Stage16R data/labels, Stage17 extractor, Stage21/22 experiments, Stage23 freeze, V1/V3 references and fit ledgers remain unchanged. Named hashing followed explicit inherited paths; no sealed Final Test or Independent Evaluation content was searched or accessed. [Preservation verification](../evidence/integration_stage3r/preservation_verification.json).

## H. Cause of disappearance

**CAUSE NOT ESTABLISHED.** No recorded deletion-operation tool call naming these exact missing paths was found in the inspected session record. The prior Git check found no tracked/history copies. This does not establish that a particular cleanup, reset, editor or automation deleted them. Generic operations outside the inspected evidence remain unverified. [Cause assessment](../evidence/integration_stage3r/cause_assessment.json).

## I. Protection against recurrence

Created an exact [source-only backup ZIP](../evidence/integration_stage3r/approved_stage3_source_backup.zip) containing the twelve recovered files, and verified every archived entry against its historical hash. The [backup manifest](../evidence/integration_stage3r/source_backup_manifest.json) binds both the archive and entries. It contains no models, datasets, sealed material, credentials or runtime environment.

The local archive is recovery redundancy, not an independent/off-machine backup. Recommend adding the active inference source/tests and approved evidence scripts to normal Git source control and keeping a separate source backup. No Git staging, commit or publication was performed. Do not add model binaries, datasets, secrets or large runtime directories merely to protect source.

## J. Stage4 readiness and final decision

The missing-approved-source blocker identified by Stage4 is resolved. The original implementation and its parity are available again, so Stage4 may resume **after explicit recovery approval**. Its post-commit hook, result table, reassessment integration, shadow transport/UI and end-to-end application testing remain separate unfinished work. No Stage4 implementation, V4 alerting, V1 replacement or cutover was performed.

**A — EXACT STAGE3 IMPLEMENTATION RECOVERED AND PARITY REVERIFIED**

V4 INTEGRATION STAGE 3R COMPLETE —
WAITING FOR APPROVAL.
''',encoding='utf-8')
assert all(sha(ROOT/p)==h for p,h in expected.items())
assert sha(stage4/'decision.json')==stage4_decision_before
files=[p for p in OUT.iterdir() if p.is_file() and p.name!='decision.json']+[report]
save('decision.json',{'decision':'A — EXACT STAGE3 IMPLEMENTATION RECOVERED AND PARITY REVERIFIED',
    'classification':'EXACT RECOVERY VERIFIED','exact_restored_files':12,'reconstructed_files':0,
    'tests_passed':54,'fixed_development_examples':128,'max_probability_difference':0,
    'stage4_resumed':False,'artifact_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files}})
print(json.dumps({'decision':'A','exact_restored':12,'tests':54,'protected_named':len(expected)}))
