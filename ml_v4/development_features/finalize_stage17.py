"""Finalize Stage17 evidence after additional fixture and saved-matrix checks."""
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from extractor import ROOT,NAMES,SPEC
from run_stage17 import EVIDENCE,MATRICES,sha,read

def update(name,data):
    (EVIDENCE/name).write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def main():
    decision=EVIDENCE/'stage17_decision.json'
    report=ROOT/'ml_v4/reports/V4_STAGE17_FEATURE_EXTRACTION_REPORT.md'
    if decision.exists() or report.exists():raise FileExistsError('Completed Stage17 cannot be overwritten')
    test=subprocess.run([sys.executable,'-B','-m','pytest','ml_v4/development_features/tests','-q','-p','no:cacheprovider'],cwd=ROOT,capture_output=True,text=True)
    assert test.returncode==0,test.stdout+test.stderr
    independent=read('ml_v4/evidence/stage17/independent_fixture_tests.json')
    independent['final_suite']={'exit_code':test.returncode,'stdout':test.stdout,'stderr':test.stderr}
    independent['initial_fixture_corrections'].append('Weekly median fixture moved fourth group off the shared week boundary; all four expected weekly counts independently specified.')
    independent['stage_order']='Initial 22-test suite passed before extraction; expanded 30-test suite passed before final decision. Extractor unchanged after extraction.'
    update('independent_fixture_tests.json',independent)
    temporal=read('ml_v4/evidence/stage17/temporal_correctness_tests.json')
    temporal['coverage'] += ['7d exact lower exclusion','5% amount equality and just outside','inclusive band endpoints','even weekly median with returning customers','nonzero 28-bin calendar median','noncanonical timestamps rejected','resolved path escape rejection (mocked resolve, no OS symlink provisioned)']
    update('temporal_correctness_tests.json',temporal)
    matrix=read('ml_v4/evidence/stage17/development_matrix_audit.json')
    quality=read('ml_v4/evidence/stage17/feature_quality_audit.json')
    fractions={'wallet_max_value_share_1h','wallet_similar_amount_share_7d','agent_new_wallet_share_7d','agent_top2_count_share_24h'}
    integer_names={f['name'] for f in SPEC['features'] if any(s in f['name'] for s in ['count','distinct','amount_minor','value_1h','value_24h','active_hours','min_length','residual_minor']) and not any(s in f['name'] for s in ['share','growth'])}
    for part in ['train','validation']:
        x=np.load(MATRICES/part/'X.npy',allow_pickle=False)
        assert x.dtype.names==NAMES
        for i,name in enumerate(NAMES):
            if i==1:continue
            values=x[name];sem=SPEC['features'][i]['missing_semantics']
            good=values[np.isfinite(values)]
            if sem.startswith('-1'):good=good[good!=-1]
            if sem.startswith('-3'):good=good[good!=-3]
            if name in integer_names:assert np.all(good==np.floor(good)),name
            if name in fractions:assert np.all((good>=0)&(good<=1)),name
            if name.endswith('coverage_days'):assert np.all((good>=0)&(good<=35)),name
            if name=='agent_top2_share_change_24h':assert np.all((good>=-1)&(good<=1))
            elif name=='agent_cash_value_skew_change':assert np.all((good>=-2)&(good<=2))
            elif name!='wallet_prior_funding_residual_minor_24h':assert np.all(good>=0),name
        assert np.all(x['wallet_count_1h']>=1)
        assert np.all(x['wallet_similar_amount_count_7d']>=1)
        for n,h in matrix['partitions'][part]['artifacts'].items():assert sha(ROOT/n)==h,n
    quality['saved_matrix_range_invariants']='PASS: integer-valued counts/amounts, share bounds, coverage 0..35, signed valid skew ranges, nonnegative eligible quantities; valid negative residuals preserved.'
    update('feature_quality_audit.json',quality)
    preservation=read('ml_v4/evidence/stage17/preservation_verification.json')
    final={n:sha(ROOT/n) for n in preservation['before']}
    assert final==preservation['before']
    preservation['final_after']=final
    v1='ml/stage14/stage14_frozen_model.pkl'
    expected=read('ml_v4/design/amendments/v4_stage15a_manifest.json')['protection']['before'][v1]
    assert sha(ROOT/v1)==expected
    preservation['additional_historical_reference_check']={v1:{'expected':expected,'actual':sha(ROOT/v1),'matches':True}}
    update('preservation_verification.json',preservation)
    family_rows=[]
    for family in 'S1 S2 S3 S4 N1 N2 N3 N4 A1 A2 A3 A4'.split():
        tr=matrix['partitions']['train']['family_support'][family]
        va=matrix['partitions']['validation']['family_support'][family]
        family_rows.append(f"| {family} | {tr['decision_points']} / 1200 | {va['decision_points']} / 300 | {tr['distinct_subjects']} / {va['distinct_subjects']} | {tr['distinct_clusters']} / {va['distinct_clusters']} | {'Met' if tr['decision_points']>=1200 and va['decision_points']>=300 else 'Shortfall'} |")
    schema_rows=[f"| {i+1} | `{f['name']}` | {f['formula']} | {f['missing_semantics']} |" for i,f in enumerate(SPEC['features'])]
    text='''# MODEL V4 — STAGE 17 DEVELOPMENT-ONLY FEATURE EXTRACTION AND FEATURE AUDIT

**A — DEVELOPMENT FEATURES COMPLETE AND VERIFIED FOR MODEL TRAINING**

The frozen 40-semantic-field extractor and hand-calculated correctness fixtures pass. Train and Validation matrices were constructed from the existing development ledgers, with exact frozen label alignment and byte-identical repeated extraction. This is technical development-feature readiness. No model was trained, selected, calibrated or independently evaluated. Family-support shortfalls and unavailable challenge custody remain unresolved.

## 1. Development-only authority and preserved precedence

The user's Stage 17 request explicitly authorizes implementation, development extraction and diagnostics after Stage 16V. It supersedes the earlier stop on these particular development activities; it does not satisfy or waive Stage 16T custody/support progression. The authorization is recorded in [development_authorization.json](../evidence/stage17/development_authorization.json).

Stage 15's feature/temporal/target definitions remain frozen. Stage 15A's scoped population amendments do not alter the feature definitions. Stage 16R's retained draw and labels remain authoritative inputs. Stage 16S's support limitations remain in force. Stage 16T's challenge protocol, Stage 16U's implementation status and Stage 16V's custody-unavailable decision are unchanged. Original Final Test and Independent Evaluation remain SEALED_QUARANTINED; their public support-policy FAIL certificates remain historical facts. No private evaluation contents, registry or challenge secret was accessed.

## 2. Implementation, inputs and storage

New source is confined to `ml_v4/development_features/`: [extractor.py](../development_features/extractor.py), [run_stage17.py](../development_features/run_stage17.py), [finalize_stage17.py](../development_features/finalize_stage17.py) and [tests/test_features.py](../development_features/tests/test_features.py). Existing source and application files were not edited.

The extractor accepts only the exact validated observable `Event` interface. It imports the existing low-level observable schema/time contract, never the evaluator, generator, labels, witnesses or private provenance. It maintains separate wallet activity, directed incoming/outgoing and agent-service histories plus first-observation timestamps. State is newly instantiated for each partition and each replay. IDs are internal join/order keys only.

The runner uses the existing fail-closed development loader with exact `train`/`validation` enums and only `warmup_observables.csv`, `transactions.csv` and `ground_truth.csv`. Hashes match the Stage 16R manifest before extraction. Frozen binary labels are read by the runner and joined by exact row-by-row transaction ID after independent feature computation; they are never supplied to the extractor. Original full-key order is retained. No scored row is filtered or resampled; warm-up rows supply history but are not training rows.

| Artifact | Train | Validation |
| --- | ---: | ---: |
| Semantic X dimensions | 60,000 × 40 | 15,000 × 40 |
| Warm-up input rows | 14,400 | 3,600 |
| y dimensions | 60,000 | 15,000 |
| Frozen target 0 / 1 | 47,770 / 12,230 | 11,970 / 3,030 |
| Extraction seconds | 31.717 | 7.689 |
| Replay seconds | 31.762 | 7.609 |
| Byte-identical replay | PASS | PASS |

Files are [Train X](../development_features/matrices/train/X.npy), [Train y](../development_features/matrices/train/y.npy), [Validation X](../development_features/matrices/validation/X.npy), and [Validation y](../development_features/matrices/validation/y.npy). Each partition also has `row_metadata.csv` containing row index, exact integer transaction ID and UTC timestamp outside X.

X uses a one-dimensional NumPy structured record array with 40 ordered named fields: 39 little-endian float64 fields and one Unicode categorical transaction-type field. Its semantic table dimensions are shown above; its physical NumPy shape is `(60000,)` or `(15000,)`. `np.load(path, allow_pickle=False)` reads it without executable pickle objects. y is uint8. Monetary/count aggregates are exact integers/rationals until final float64 conversion. Counts and amounts retain integer-valued outputs on these data.

No one-hot expansion was applied, so no 42-column encoding order is invented or claimed frozen. Transaction type retains the observable categories `wallet_to_wallet`, `cash_in`, `cash_out`, corresponding to W2W/Cash-In/Cash-Out. Future model preprocessing must explicitly freeze its numeric encoding and marker treatment; no scaler, imputer, calibration or learned transformation was fitted here.

## 3. Exact semantic fields

The full ordered definitions, eligibility, domains, direct-target-component disclosures, dtype and path-selection rule are copied into [feature_schema_audit.json](../evidence/stage17/feature_schema_audit.json). Frozen source specification hashes bind that record. The implementation uses no additional features.

| # | Field | Frozen formula | Missing semantics |
| --- | --- | --- | --- |
'''+ '\n'.join(schema_rows)+'''

## 4. Temporal and numerical correctness

All timestamps are canonical UTC at integer microseconds. Full keys must strictly increase, transaction IDs must be unique, and each row is computed before current-event state insertion. Same-time smaller IDs can contribute; larger IDs cannot. Recent intervals are open below and closed above; preceding 28-day baselines are disjoint. Calendar-day counts use UTC midnight and the explicit S3 half-open 28-bin exception. No frozen field uses a separate 30-day window, so none was added from the request's general window summary.

A1 historical growth/newness requires the actual first observed service at or before the 35-day boundary and at least 12 services strictly inside its baseline. The coverage display never substitutes for the timestamp gate. Recent distinct counts remain available at cold start. Agent service roles include receiver-serviced assisted W2W once, while W2W never contributes cash values/counts. Valid negative concentration/skew changes remain distinct from -3; valid negative N4 residuals remain distinct from NaN.

N3 enumerates every simple chronological topology path of one to five prior edges within seven days. There is no path truncation or amount-based topology filtering. The selected route minimizes the exact rational maximum of adjacent amount ratio and its reciprocal, then length, then full-key sequence. Monotonicity of log makes this ranking equivalent to the frozen maximum absolute log-ratio ordering; only the final log descriptor is float64. Current amount never selects the route. N4 uses the smallest-key prior incoming W2W anchor within 24 hours, counts funding/outward roles once, and excludes the current amount from the residual.

## 5. Independent calculations and test results

**30 pytest cases passed.** The initial 22-case suite passed before extraction; eight additional cases/parameter instances passed before this final decision. Expectations are independently hand-derived in the test file, including a complete 40-field cold-start vector and nontrivial wallet, network, agent, funding, concentration and cash examples. Tests do not invoke the target evaluator or use its witnesses. This is independent reference calculation within the same developer environment, not an independent external audit.

Coverage includes feature order/dtypes; exact amounts/counts; hour/day/seven-day boundary equality; 5% amount and band endpoints; disjoint baselines; zero and nonzero daily medians; fractional weekly medians; exact 35-day age and baseline minimum support; incoming observation age; all missing markers; valid signed values; equal-time IDs; future append and identity-renaming invariance; network direction; N3 chronology, 1..5 versus 6 edges, competing route selection and tie-breaks; N4 anchors/residuals; cash/assisted roles; fresh partition state; forbidden-field rejection; unauthorized partition/file rejection and resolved path escapes. The path-escape fixture mocks resolution; it does not claim provisioned OS symlink permissions.

Initial failures were in fixture expectations: service dates outside A3/A4 baselines, weekly events crossing a shared week boundary, and raw NaN equality assertions. Dates and marker-aware assertions were corrected after checking the frozen boundaries. No feature definition or target was changed. Final failures: none. Full output and qualifications are in [independent_fixture_tests.json](../evidence/stage17/independent_fixture_tests.json) and [temporal_correctness_tests.json](../evidence/stage17/temporal_correctness_tests.json).

## 6. Matrix quality, leakage and resource audit

Both partitions passed complete row/label/ID alignment, separate history/entity/transaction-ID checks, exact schema, marker-aware finite validity and numeric range checks. NaN occurs only where permitted for the N4 funding residual. There are no infinities, constant columns or identical column pairs. There are 75 repeated feature vectors in Train and 2 in Validation; these are retained observations, not duplicate transaction IDs, and no rows were deduplicated.

| Descriptor | Train | Validation |
| --- | ---: | ---: |
| A1 growth missing rows | 18,858 | 4,828 |
| N4 residual missing rows | 49,076 | 12,308 |
| Valid N4 residual minimum, cents | -4,741,603 | -2,315,918 |
| Maximum topology path count | 20 | 13 |

Column-wise missing fractions, valid quantiles/ranges, category counts and Train/Validation differences are in [feature_quality_audit.json](../evidence/stage17/feature_quality_audit.json). Differences are descriptive; no transformations, clipping or selection were fitted to reduce them. Missingness and repeated synthetic behaviour can be informative and remain limitations for future model audits.

The observed peak process working set was 295,960,576 bytes (about 282.25 MiB), a Windows process high-water measurement including inputs, replay and audits, not an isolated extractor allocation. Runtime was Python 3.14.3 / NumPy 2.4.3; source/schema/input/output SHA-256 records accompany this report. Both full extractions were repeated in fresh state, with byte-identical NPY serialization. Reproducibility is demonstrated in this recorded runtime, not guaranteed across arbitrary dependencies or hardware.

Static import/interface review confirms the extractor has no evaluator or generator import. X has no IDs, absolute timestamps, partition indicator, labels, rule flags, scores, private origins/archetypes, event/context roles or private activation. Frozen behavioural components that overlap target components remain explicitly disclosed, rather than being described as independent labels. Full details are in [leakage_audit.json](../evidence/stage17/leakage_audit.json) and [development_matrix_audit.json](../evidence/stage17/development_matrix_audit.json).

## 7. All-family support remains unchanged

These counts are taken from the saved Stage 16S development evidence; no family labels were recalculated or changed. Rows carrying multiple families overlap. Subjects and clusters are not independent sample sizes.

| Family | Train / minimum | Validation / minimum | Subjects Train / Validation | Clusters Train / Validation | Count objectives |
| --- | ---: | ---: | ---: | ---: | --- |
'''+ '\n'.join(family_rows)+'''

The nine shortfalls S1/S2/S4/N1/N3/N4/A2/A3/A4 remain. In particular, Validation S2 has only 23 positives across 7 subjects/7 clusters; S4 has 16 across 12/12. N3 has 130 positives and A4 has 222, both below 300. S3/N2/A1 meeting count objectives does not establish model quality or representative uncertainty. Technical feature readiness cannot establish reliable twelve-family learning/evaluation, repair the original holdouts or manufacture evidence for sparse families.

## 8. Preservation and limits

All six authorized development observable/history/label files match the Stage 16R manifest before extraction and remain unchanged afterward. The named preservation inventory also covers frozen design/amendment/challenge records, prior stage public evidence/source, V3 model/extractor/preprocessing, experimental API/dashboard and Flask entrypoint. The V1 production artifact separately matches its historical SHA-256. No application, MySQL, V1/V2/V3 model or integration source was modified.

The detailed inventory and before/after values are in [preservation_verification.json](../evidence/stage17/preservation_verification.json). This is an explicit named-file scope, not an inventory of every disk file. Sealed bytes are excluded and unread. Stage 16V's incomplete broad Stage 15A historical snapshot remains documented; no archive was restored and no older manifest or historical file was rewritten to suppress that limitation.

The feature contract deliberately omits some predicate components and N3 retains a lossy selected-route summary. Synthetic separability, correlated direct components, cold starts, development-data reuse and sparse family support remain scientific risks. Feature correctness is not evidence of actual laundering detection, regulatory effectiveness or model validation. Challenge-generation custody and original independent evaluation remain blocked.

## 9. Reproduction and deliverables

Read-only fixture command: `python -B -m pytest ml_v4/development_features/tests -q -p no:cacheprovider`.

`run_stage17.py` verifies named inputs, runs the fixtures, extracts/replays each partition and records audits; it refuses existing output directories. `finalize_stage17.py` performs final fixture/range/hash checks and writes the report/decision; it refuses an existing completed report or decision. Reproduction requiring regenerated matrices belongs in a separate authorized output workspace, preserving this result. No code here fits a model.

Required evidence: [schema](../evidence/stage17/feature_schema_audit.json), [temporal tests](../evidence/stage17/temporal_correctness_tests.json), [independent fixtures](../evidence/stage17/independent_fixture_tests.json), [matrix audit](../evidence/stage17/development_matrix_audit.json), [quality](../evidence/stage17/feature_quality_audit.json), [leakage](../evidence/stage17/leakage_audit.json), [preservation](../evidence/stage17/preservation_verification.json), [decision and artifact hashes](../evidence/stage17/stage17_decision.json). The additional development authorization record documents this stage's narrow permission.

## 10. Decision

**A — DEVELOPMENT FEATURES COMPLETE AND VERIFIED FOR MODEL TRAINING**

All required implementation, fixture and development-matrix checks pass within the stated scope. This permits these artifacts to be considered in a separately authorized model-development plan; it does not start training or waive support, custody or evaluation requirements. No model, hyperparameter search, threshold selection, additional transaction generation, sealed evaluation access or automatic Stage 18 progression occurred.

V4 STAGE 17 COMPLETE — WAITING FOR APPROVAL.
'''
    report.write_text(text,encoding='utf-8',newline='\n')
    paths=[report,*EVIDENCE.glob('*.json'),ROOT/'ml_v4/development_features/extractor.py',ROOT/'ml_v4/development_features/run_stage17.py',Path(__file__),ROOT/'ml_v4/development_features/tests/test_features.py']
    for part in ['train','validation']:paths.extend((MATRICES/part).iterdir())
    decision_data={'stage':'17','decision':'A — DEVELOPMENT FEATURES COMPLETE AND VERIFIED FOR MODEL TRAINING',
        'scope':'Technical development-feature readiness only; no training or independent evaluation authorization.',
        'required_tests_and_audits':'PASS','pytest_cases':30,'external_independent_audit':False,'semantic_dimensions':{'train':[60000,40],'validation':[15000,40]},
        'family_support_shortfalls_retained':['S1','S2','S4','N1','N3','N4','A2','A3','A4'],
        'challenge_custody':'BLOCKED; Stage16V C unchanged','original_evaluations':'SEALED_QUARANTINED; not accessed',
        'models_trained':0,'threshold_search':False,'new_transactions_generated':0,'automatic_stage18':False,
        'preserved_inventory_count':len(final),'historical_preservation_gap_retained':True,
        'artifact_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in paths},'manifest_self_hash_excluded':True}
    update('stage17_decision.json',decision_data)
    print(test.stdout);print(f'Finalized Stage17: {len(final)} preserved paths; V1 historical reference matches; {len(paths)} artifact hashes.')

if __name__=='__main__':main()
