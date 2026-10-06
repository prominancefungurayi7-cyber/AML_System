"""Render the single main Stage 10A report from completed audit records."""
import json
from pathlib import Path
from stage10a_contract import NAMES, FEATURES, BASELINES
from stage10a_protection import ROOT, PUBLIC, sha, snapshot, compare

R=ROOT/'reports'

def load(name): return json.loads((R/name).read_text(encoding='utf-8'))
def fmt(v):
    if v is None: return 'N/A'
    if isinstance(v,float): return f'{v:.6g}'
    return str(v)
def table(headers,rows):
    return '\n| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(fmt(v) for v in row)+' |\n' for row in rows)+'\n'

def main():
    stats=load('stage10a_feature_statistics.json'); shift=load('stage10a_shift_audit.json')
    tests=load('stage10a_temporal_tests.json'); oracle=load('stage10a_oracle_leakage.json')
    repro=load('stage10a_reproducibility.json'); protect=load('stage10a_protection.json')
    freeze=load('stage10a_contract_manifest.json')
    family_audit=load('stage10a_family_oracle_leakage.json')
    assert all(x['result']=='PASS' for x in (tests,oracle,repro,protect,family_audit))
    assert compare(protect['before'],snapshot())['result']=='PASS'
    for name,digest in freeze['hashes'].items(): assert sha(ROOT/name)==digest
    funding=[stats[p]['statistics']['wallet_prior_funding_age_hours']['observed_values']['maximum'] for p in ('train','validation')]
    text=f'''# MODEL V3 - STAGE 10A SEMANTIC CORRECTION AND RE-AUDIT

**Result: PASS for the Stage 10A feature correction and audit scope.** 32 corrected features were independently extracted twice for 60,000 Train and 15,000 Validation transactions. Both serialized output sets matched. All {tests['tests_run']} expanded hand-test methods passed, and frozen targets were preserved. No classifier was trained or evaluated.

This is the **single main report**. It contains the correction decisions, matrix results, test expectations, distributions, shift, leakage audit, reproducibility, protection and full corrected contract. The separately requested Markdown files are supporting entry points; machine-readable records retain the detailed counts and hashes.

## 1. Scope, status and artifact use

Use `ml_v3/features/development/stage10a/train/` and `ml_v3/features/development/stage10a/validation/` for the corrected development artifacts. Each contains `X.csv`, `y.csv`, `row_ids.csv` and `feature_names.json`. Their parent `version.json` identifies `{freeze['version']}` and its contract digest. Original Stage 10 matrices under `features/development/train/` and `validation/` are **superseded**, preserved unchanged as audit evidence. The original contract and overall report were also preserved.

The frozen V3 raw dataset, ground truth and predicates were not changed. Only Train/Validation transactions were extracted. Targets were aligned by transaction ID from `decision_point_target`; diagnostic family evidence was used after extraction solely for the leakage audit. Feature extraction projects eight observable event fields and never receives target, family, witness, onset or provenance fields as inputs.

No Final Test or Independent Evaluation directory was enumerated or data file opened in this stage. Public commitment certificates were checked by their explicit allowed paths. This is a feature-semantics result, not model performance or permission to begin training. No fitted preprocessing, threshold search or application integration took place.

## 2. Resolution of all ten findings

| Finding | Correction and verification |
|---|---|
| A. N3 temporal paths | Traversal enforces `key(e1) < ... < key(ek) < key(T)`, simple nodes, 1..5 edges, open 7d lower boundary. Hand cases include reversed/partial-reversed paths, ties, five/six edges, future edges and current closure. |
| B. Equal timestamps | All histories filter by full `(UTC timestamp, integer ID)` keys. Smaller same-time IDs are prior; larger IDs are future. State updates once after emission. Network, wallet, agent, funding, coverage, baseline and path cases are tested. |
| C. Funding window | Earliest eligible prior W2W anchor must be inside `(t-24h,t]`. Cash-In contributes only from that anchor onward. Every observed age is nonnegative and strictly below 24h; the former ~4318h age is gone. |
| D. Baselines | Every recent window has its disjoint preceding 28d baseline. Uncapped first-observation coverage and relevant event minima are enforced. Eligibility cannot be supplied by recent events. |
| E. Missing values | Nonnegative unavailable quantities retain -1; signed changes use -3 outside their valid domains. Raw cash skews retain valid -1 and have no missing marker. No feature-count increase. |
| F. Novelty | Fraction of DISTINCT recent wallets absent from the baseline union. Three visits to new plus one visit to old gives 1/2, not 3/4. |
| G. Oracle audit | Observable-input projection, private-field mutation, source review, direct/inverse target checks, single-value mappings, monotone separation, all 496 numeric pairs and fixed condition combinations; frozen family outcomes also checked. |
| H. Serialized repeatability | Two independent stateful extractions reload frozen development inputs, write separate temporary file sets, round-trip them and compare numeric/target/ID/order values and every output hash. |
| I. Protection | Explicit before/after inventories cover application/V1/V2 allowlists, frozen V3 development inputs, design, earlier reports/matrices and named public commitments. No holdout traversal. |
| J. Contract freeze | Versioned corrected contract, ordered 32-column schema and implementation hashes were written before full extraction. Original contract digest is recorded as observed now, without a claim of a historical prehash. |

An additional correction makes assisted W2W use the **sender** for structuring/funding, while agent-service summaries still use the explicitly serviced wallet. Receiver receipts establish observable coverage and inflow history without becoming outgoing wallet activity.

### Authority resolutions

The [Stage 8 onset contract](../design/V3_SCENARIO_ONSET_CONTRACT.md) and [feature architecture](../design/V3_FEATURE_ARCHITECTURE_PROPOSAL.md) distinguish feature summaries from full ground-truth predicates. N3's architectural feature selects a chronological path by topology; current/first-edge amount is a separate ratio. It does not apply the full predicate's adjacent-amount or return-ratio gates. Tests deliberately retain a chronological path with an amount ratio outside those gates. The selected path is a lossy summary when several paths exist.

N4's frozen anchor is a prior **W2W inflow**. A Cash-In-only history therefore has no qualifying anchor, including Cash-In 23h59m earlier. Cash-In at/after an eligible W2W anchor contributes funding and is within the 24h interval. Broadening the anchor to Cash-In alone would alter the frozen design. Every W2W is evaluated as an outward edge of its sender; no private episode role is inferred to force an inbound/funding label.

## 3. Matrix integrity and feature order
'''
    text+=table(['Partition','Rows','Columns','Target 0','Target 1','NaN','Infinity','Duplicate IDs','Range check'],
                ([p,s['rows'],s['columns'],s['target_counts']['0'],s['target_counts']['1'],s['nan_count'],s['infinity_count'],s['duplicate_row_ids'],s['range_check']] for p,s in stats.items()))
    text+='The logical and serialized counts are both 32: current 3, structuring 7, network 10, agent 9, coverage 3. CSV stores decimal numeric text; extraction uses Python binary64 floats after integer minor-unit arithmetic. Counts/indicators/path length are integer-valued. IDs are separate from X. Exact ordered definitions, ranges, units, cold-start and temporal rules are reproduced in Appendix A.\n'
    text+=table(['Position','Feature','Domain','Valid range','Missing marker'],
                ([i,f'`{f[0]}`',f[1],f"{f[5]}..{f[6] if f[6] is not None else 'unbounded'}",f[7] if f[7] is not None else 'none'] for i,f in enumerate(FEATURES,1)))
    text+='Funding age has an open upper limit: valid values are **[0,24)** hours. The observed maxima are '+', '.join(f'{p}: **{v:.9g}h**' for p,v in zip(('Train','Validation'),funding))+'.\n'
    text+='''
## 4. Temporal and manually calculated hand tests

Tests use synthetic in-memory events, integer IDs and explicit timestamps/amounts. They do not read holdouts or use model output. Values below are manually specified expected results asserted by the test suite. The test count counts methods; individual methods include multiple subcases.
'''
    text+=table(['N3 case','Expected path length','Expected current/first-edge ratio'],[
        ['r→m then m→s; current s→r ($50 versus first $200)',2,.25],
        ['Reversed chronological two-edge route',0,-1],['Partially reversed three-edge route',0,-1],
        ['Same timestamp, increasing IDs 1→2 then current 3',2,1],['Route needs an edge after current',0,-1],
        ['Only a six-edge route',0,-1],['No return route',0,-1],['Current reciprocal closure ($50 / $200)',1,.25],
        ['Valid five-edge route',5,1],['Latest-first-edge tie ($100 / $200)',1,.5],
        ['Valid chronology, monetary ratio outside predicate bands',2,2000]])
    text+=table(['Other hand case','Expected output'],[
        ['Isolated $100 W2W','Wallet count 1, value $100, day/hour 1, cluster share 1, band share 0; no baseline/path/funding; coverage 0'],
        ['Four wallet events 7000,7100,100,7000 across hours 0,1,2,2','Last-hour count 2; 24h value 21200; day count 4; active hours 3; cluster and band shares .75'],
        ['Four distinct collection sources / dispersion recipients','Breadth 4 and event count 4'],
        ['W2W funding $100 at 23h59m; current $50 out','Share .5; age 23.9833333333h'],
        ['Anchor exactly 24h old / 24h+1s / future','Share -1 and age -1'],
        ['Two W2W anchors $100+$50; later Cash-In $50; two $50 outflows','F=200, O=100, share .5; earliest anchor age 2h'],
        ['Cash-In only; current outbound','No W2W anchor: share -1 and age -1'],
        ['Current Cash-In itself','Share 0; age -1'],
        ['ID1 same-time $100 inflow; ID2 $50 Cash-Out; ID3 same-time future inflow','At ID2: receiver count 1, funding share .5, age 0, agent service count 2'],
        ['Wallet baseline 4 events plus full coverage / only 3 events','Acceleration 1 / missing -1; recent events cannot fill baseline minimum'],
        ['1344 wallet baseline events, two recent events','Expected hourly baseline 2; acceleration 2/2=1'],
        ['Agent 12 baseline services, five recent services','Recent count 5; acceleration 5'],
        ['Recent old + new,new,new; one old wallet per baseline week','Growth ratio 2; DISTINCT novelty 1/2'],
        ['Five equally served baseline wallets; four recent events at one wallet','Top2 recent 1; baseline .4; change .6'],
        ['Same baseline; four different recent wallets','Top2 recent .5; change .1'],
        ['Cash-In dominated / Cash-Out dominated / balanced','Signed value/count skews -1 / +1 / 0'],
        ['Baseline all Cash-Out; recent cash balanced','Valid signed change -1 retained; unavailable change is -3'],
        ['First observation age 0 / 1h / 28d / 50d','Coverage 0 / 1/24 / 28 / 28 days'],
        ['Exact recent lower boundary / baseline lower / baseline upper','Exclude / exclude from count (may establish coverage) / include'],
        ['Amount $50→$100 on existing two-edge path with $200 first edge and $100 funding','Path length stays 2; ratio .25→.5; share .5→1; funding age unchanged'],
    ])
    text+=f'**Executed: {tests["tests_run"]} methods, no failures or errors.** Future additions and mutations leave earlier vectors identical across wallet, graph, funding and agent fixtures. Current-amount perturbation checks every column against the allowed dependency set, with exact examples for path/funding. Endpoint changes may legitimately select another history; no claim is made that endpoint-dependent features must remain unchanged. Same-time IDs below and above current are tested, as are disjoint baseline boundaries, lexicographic path ties, partition state reset and duplicate-ID rejection.\n\n'
    text+='Executed methods:\n\n'+''.join(f'- `{n.split(".")[-1]}`\n' for n in tests['test_names'])
    text+='\n## 5. Baseline availability and missingness\n\nBaseline B(L) is `(t-L-28d,t-L]`; recent R(L) is `(t-L,t]`. Windows do not overlap. Full observation requires first prior observation at or before the baseline lower boundary. The displayed 28d coverage cap is never used to infer 29d or 35d eligibility. Rate denominators use `max(1, expected count)`; the growth denominator is `max(1, median of four weekly distinct counts)`. The A2 comparator pools 28d and ranks its top two wallets independently of the recent 24h top two.\n'
    text+=table(['Feature','Recent','Baseline minimum','Other requirements','Missing','Train unavailable','Validation unavailable'],
        ([f'`{NAMES[i]}`',L,str(count)+' '+stream,extra,FEATURES[i][7],stats['train']['statistics'][NAMES[i]]['missing_fraction'],stats['validation']['statistics'][NAMES[i]]['missing_fraction']] for i,(L,stream,count,extra) in BASELINES.items()))
    text+='Every missing fraction below uses the column-specific marker. Raw skews have no unavailable marker: -1 means fully Cash-In dominated. Signed changes may legitimately equal -1; their unavailable value is -3. All count/value/ratio range checks exclude only the documented marker. No availability flag encodes a reference outcome.\n'
    text+=table(['Feature','Train valid -1 count','Validation valid -1 count'],
        ([f'`{NAMES[i]}`',stats['train']['statistics'][NAMES[i]]['legitimate_negative_one_count'],stats['validation']['statistics'][NAMES[i]]['legitimate_negative_one_count']] for i in (25,26,27,28)))
    text+='\n## 6. Corrected feature distributions\n\nObserved summaries exclude the documented missing marker. Zero fraction is over all rows. Missing fractions are reported separately. Binary features are not flagged near-constant merely for having two distinct values: the corrected rule requires modal frequency ≥99%. Tail-span/IQR diagnostics and summaries including sentinels are retained in JSON; large ratios when IQR=0 are descriptive flags, not grounds for changing features.\n'
    for p in ('train','validation'):
        text+=f'\n### {p.title()}\n'
        rows=[]
        for n in NAMES:
            s=stats[p]['statistics'][n]; v=s['observed_values']
            rows.append([f'`{n}`']+[v.get(k) for k in ('minimum','maximum','mean','std','median','q01','q05','q95','q99')]+[s['all_values']['zero_fraction'],s['missing_fraction'],v.get('distinct_count')])
        text+=table(['Feature','Min','Max','Mean','SD','Median','Q01','Q05','Q95','Q99','Zero fraction','Missing fraction','Observed distinct'],rows)
        constants=[n for n in NAMES if stats[p]['statistics'][n]['all_values']['constant']]
        near=[n for n in NAMES if stats[p]['statistics'][n]['all_values']['near_constant']]
        text+=f'Constant columns including encoded missingness: {", ".join(constants) or "none"}. Near-constant columns by the ≥99% modal rule: {", ".join(near) or "none"}.\n'
    text+='\n## 7. Train/Validation shift\n\nDifferences are Validation minus Train. Means exclude unavailable markers. Missingness and zero fractions are over all rows; their differences are proportions, not percentage-point numbers. Units differ across columns, so raw mean differences are not ranked as comparable effect sizes. Coverage, topology, funding and novelty are retained as originally specified regardless of shift.\n'
    text+=table(['Feature','Train observed mean','Validation observed mean','Mean difference','Train missing','Validation missing','Missing difference','Zero-fraction difference'],
        ([f'`{n}`']+[shift[n][k] for k in ('train_observed_mean','validation_observed_mean','observed_mean_difference','train_missing_fraction','validation_missing_fraction','missing_fraction_difference','zero_fraction_difference')] for n in NAMES))
    text+='\n## 8. Oracle-leakage audit\n\n**PASS within the documented checks.** The extractor imports no reference evaluator, old V2 feature code or classifier. AST review checks forbidden private-field literals and imports; explicit observable projection and adversarial metadata mutations provide additional evidence. Source review below considers whether each feature group directly implements an entire reference conjunction. Audit family outcomes come from the frozen development witness ledger only after X is extracted; they do not enter X.\n'
    text+=table(['Reference family','Why the feature summary is not a complete predicate'],oracle['source_review']['reference_predicate_review'].items())
    text+='The initial runner used short family codes against a ledger containing full family names, so its additional family checks were uninformative. A separate audited diagnostic maps all 12 full names explicitly, verifies that the union of family evidence equals each frozen target, and repeats the checks against unchanged published matrices. The initial record and frozen extraction source are preserved; `stage10a_family_oracle_leakage.json` is the authoritative corrected family diagnostic. This reporting/audit correction does not change feature semantics, X or y.\n'
    for p in ('train','validation'):
        o=oracle['partitions'][p]
        exact_pairs=[(n,v) for n,v in o['two_feature_mappings'].items() if v['exact_mapping_on_sample']]
        exact_singles=[n for n,v in o['single_features'].items() if v['exact_mapping_on_sample']]
        text+=f'\n### {p.title()} leakage checks\n\nChecked 32 individual value mappings, 32 direct/inverse target columns, monotone one-cutoff separation, **{o["pairs_checked"]} two-feature value mappings**, {len(o["fixed_condition_names"])} fixed observable conditions and **{o["fixed_pair_and_or_checked"]} fixed AND/OR combinations** (including inverse equivalence). Exact direct target columns: {o["exact_direct_columns"]}; exact monotone target separators: {o["exact_monotone_equivalences"]}; exact fixed target combinations: {o["exact_fixed_combination_equivalences"]}.\n\n'
        text+=f'Exact single-feature lookup mappings on this finite sample: {exact_singles}. Exact two-feature lookup mappings: {len(exact_pairs)}. Such mappings may be vacuous when pairs identify rows; singleton and contradictory-key counts are reported for all pairs in JSON. They are not evidence of a portable oracle without source or repeated-value support.\n'
        text+=table(['Single feature','Distinct values','Contradictory value groups','Rows in contradictory groups','Singleton fraction'],
            ([f'`{n}`',v['distinct_keys'],v['contradictory_keys'],v['rows_in_contradictory_keys'],v['singleton_fraction']] for n,v in o['single_features'].items()))
        if exact_pairs:
            text+=table(['Exact finite-sample pair mapping','Distinct pairs','Singleton fraction'],([n,v['distinct_keys'],v['singleton_fraction']] for n,v in exact_pairs))
        text+=table(['Frozen family outcome','Positive support','Negative support','Direct / monotone / fixed combination equivalence check'],
                    ([family,family_audit['partitions'][p]['support_counts'][family].get('1',0),family_audit['partitions'][p]['support_counts'][family].get('0',0),v['result']] for family,v in family_audit['partitions'][p]['checks'].items()))
    text+='''
Strong behavioural association is allowed. No feature was added, dropped or tuned using these results. The audit does not exclude arbitrary nonlinear/high-order encodings, near-perfect separators or generator shortcuts. Monotone checks look for exact separation, and the fixed conjunction checks are not exhaustive. No learned classifier, optimized cutoff, model accuracy, F1, ROC-AUC, PR-AUC or feature importance was computed. Descriptive condition constants are the predeclared synthetic-contract checks, not a fitted classification threshold.

## 9. Contract freeze and serialized reproducibility
'''
    text+=table(['Record','Value'],[
        ['Version',freeze['version']],['Contract frozen UTC',freeze['frozen_at_utc']],
        ['Run A started UTC',repro['runs']['run_a']['started_at_utc']],['Run B started UTC',repro['runs']['run_b']['started_at_utc']],
        ['Completed UTC',repro['finished_at_utc']],['Runner duration seconds',repro['runtime_seconds']],
        ['Original Stage 10 contract SHA-256 observed in this stage',freeze['original_stage10_contract_hash_observed_now']],
        ['Corrected contract SHA-256',freeze['hashes']['reports/V3_STAGE10A_FEATURE_CONTRACT.md']],
        ['Freeze-manifest SHA-256',repro['contract_manifest_sha256']]])
    text+='The two extractions reload frozen input tables and start empty histories independently. Each writes its own temporary serialized set before comparison. CSV round-trip values, numeric matrices, targets, row IDs, row/feature order and all four file hashes match. The first set is copied to the versioned development directory and checked again. Temporary sets were removed after comparison; their recorded hashes are below. No original matrix was reused.\n'
    text+=table(['Partition','File','Run A SHA-256','Run B identical; published identical'],
        ([p,n,f'`{digest}`',True] for p in ('train','validation') for n,digest in repro['runs']['run_a']['partitions'][p]['hashes'].items()))
    text+='Each y value was mapped from frozen ground truth using its transaction ID, with exact ID-set equality and fixed target counts. The corresponding y-file hashes above identify the serialized mapped labels; the source ground-truth hashes below identify the untouched authority.\n'
    text+=table(['Partition','Ground truth SHA-256'],([p,repro['runs']['run_a']['partitions'][p]['ground_truth_file_sha256']] for p in ('train','validation')))
    text+='\n## 10. Protection and public commitment\n'
    text+=f'**PASS:** {len(protect["before"]["files"])} protected files before and {len(protect["after"]["files"])} after; changed set `{protect["changed"]}`. All 14 explicitly listed frozen development inputs also match their Stage 9 manifest. The inventory contains file paths and digests, with exact inclusion/exclusion scope in `stage10a_protection.json`.\n\nExplicit traversed directories:\n\n'+''.join(f'- `{p}`\n' for p in protect['before']['scope'])
    text+='\nAdditional explicit files include selected root application/configuration files, the frozen V3 reference/generator/access sources, previous Stage 9/10 reports, development manifest and two named public certificates. No dataset root or evaluation subtree is recursively scanned. Protection is a certificate for this allowlist, not every file on disk. Prohibited holdout bytes and unpartitioned historical datasets are excluded.\n'
    text+=table(['Public artifact','Before SHA-256','After SHA-256'],([p,protect['before']['public'][p],protect['after']['public'][p]] for p in PUBLIC))
    text+='The two public certificates agree on the private-manifest commitment and each certificate is unchanged. This verifies the public commitment metadata; it does **not** freshly verify the continued integrity of unread holdout bytes. Such verification belongs to a separately authorized final evaluator.\n'
    text+='''
## 11. Limitations, reproducible entry points and decision

All ten required findings are resolved for the corrected feature implementation and stated audit scope. PASS is based on semantic review, exact synthetic examples, full development range/integrity checks, descriptive leakage checks, independent serialized agreement and protection checks together.

This stage does not certify the frozen reference evaluator's implementation against every written Stage 8 predicate. Targets are preserved as explicitly required. Selected-path compression, proxy funding attribution, denominator floors, sparse baselines, pooled-28d versus recent-24h concentration, partition-local observation and synthetic ground truth remain experiment limitations. Baseline missingness is expected when eligibility fails. Coverage of tests and leakage combinations is finite.

Future preprocessing must use per-column missing markers, preserving legitimate negative values; any fitted scaling, clipping or imputation must use Train only. No such preprocessing was fitted here. Model training remains a later, separately authorized stage.

Implementation: `src/stage10a_pipeline.py`, `src/stage10a_contract.py`, `src/stage10a_audit.py`, `src/stage10a_protection.py`. Orchestration: `src/run_stage10a.py`; reporting: `src/report_stage10a.py`. Commands from the repository root:

```powershell
python -B -m unittest discover -s ml_v3/tests -p test_stage10a_features.py -v
python -B ml_v3/src/run_stage10a.py
python -B ml_v3/src/audit_stage10a_families.py
python -B ml_v3/src/report_stage10a.py
```

The extraction command creates new artifacts exclusively and refuses to overwrite an existing corrected run. To reproduce the whole workflow, use a fresh authorized development checkout with the original protected inputs, the recorded source versions and a fresh `stage10a_protection_before.json` generated by `stage10a_protection.py`; preserve existing run evidence. The report command reads the completed audit JSON and rewrites only the new Stage 10A report entry points.

### Evidence index

| File | Evidence |
|---|---|
| [stage10a_contract_manifest.json](stage10a_contract_manifest.json) | Ordered schema, original/current hashes, source/design digests and freeze timestamp |
| [stage10a_feature_statistics.json](stage10a_feature_statistics.json) | Matrix integrity, ranges, all/observed distributions, missingness and target-conditional summaries |
| [stage10a_shift_audit.json](stage10a_shift_audit.json) | Per-feature mean, zero and unavailable shifts |
| [stage10a_temporal_tests.json](stage10a_temporal_tests.json) | Executed test names and full captured test log |
| [stage10a_oracle_leakage.json](stage10a_oracle_leakage.json) | Source review, 32 single and 496 pair mappings per partition, fixed condition and frozen-family checks |
| [stage10a_family_oracle_leakage.json](stage10a_family_oracle_leakage.json) | Corrected full-name family lookup, support counts and predicate-outcome equivalence checks; supersedes the initial uninformative family lookup |
| [stage10a_reproducibility.json](stage10a_reproducibility.json) | Independent-run timings, exact equality checks, source target and output hashes |
| [stage10a_protection.json](stage10a_protection.json) | Explicit before/after file inventories, changes, public-certificate hashes and scope |

## Appendix A. Complete corrected feature contract

The following is the frozen corrected contract reproduced verbatim, with headings nested for this report. Its separately hashed file remains the authority for the feature version.

'''
    contract=(R/'V3_STAGE10A_FEATURE_CONTRACT.md').read_text(encoding='utf-8')
    text+='\n'.join('#'+line if line.startswith('#') else line for line in contract.splitlines())+'\n'
    text+='\nV3 STAGE 10A COMPLETE — WAITING FOR APPROVAL.\n'
    (R/'V3_STAGE10A_CORRECTION_REPORT.md').write_text(text,encoding='utf-8',newline='\n')
    for name,title,section,brief in (
        ('TEMPORAL_AUDIT','TEMPORAL AUDIT','4-temporal-and-manually-calculated-hand-tests',f'{tests["tests_run"]} expanded hand-test methods passed; exact expected cases and scope are in the main report.'),
        ('ORACLE_LEAKAGE_AUDIT','ORACLE-LEAKAGE AUDIT','8-oracle-leakage-audit','No direct encoding was found by the documented source, metadata, single/pair and fixed-condition checks. Finite-sample and non-exhaustive limits apply.'),
        ('REPRODUCIBILITY','REPRODUCIBILITY','9-contract-freeze-and-serialized-reproducibility','Two independent extractions wrote separate serialized sets and matched numeric values, targets, IDs, orders and all output hashes.'),
        ('PROTECTION','PROTECTION','10-protection-and-public-commitment',f'{len(protect["before"]["files"])} protected allowlisted files and the public commitment certificates are unchanged. Holdout data bytes were not opened.')):
        (R/f'V3_STAGE10A_{name}.md').write_text(f'# MODEL V3 - STAGE 10A {title}\n\n**Result: PASS within the documented scope.** {brief}\n\nThe complete evidence, details and limitations are consolidated in [the single Stage 10A report](V3_STAGE10A_CORRECTION_REPORT.md#{section}).\n',encoding='utf-8',newline='\n')
    (ROOT/'features/development/README_STAGE10A.md').write_text('# V3 development feature versions\n\nUse `stage10a/train/` and `stage10a/validation/`: corrected 32-feature contract `v3_stage10a_features_1`. The original sibling `train/` and `validation/` directories are superseded Stage 10 audit artifacts; preserve them unchanged.\n\n[Complete Stage 10A report](../../reports/V3_STAGE10A_CORRECTION_REPORT.md). No model training was performed in this stage.\n',encoding='utf-8',newline='\n')
    print(R/'V3_STAGE10A_CORRECTION_REPORT.md')

if __name__=='__main__': main()
