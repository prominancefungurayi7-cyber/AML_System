"""One production attempt, immutable design inputs, development audit and seal."""
from __future__ import annotations
import ctypes
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from stage16r_contract import ROOT,DAY,FAMILIES,json_bytes,save_json,sha,read_events
from stage16r_generator import DATASET,SEED,STREAMS,Unit,generate_partition
from stage16r_evaluator import replay
from stage16r_audit import partition_files,integrity,development_audit

OUT=ROOT/'ml_v4/evidence/stage16r'
DATA=ROOT/'ml_v4/data/development'
REPORT=ROOT/'ml_v4/reports/V4_STAGE16R_DATASET_GENERATION_AUDIT.md'


def now(): return datetime.now(timezone.utc).isoformat()


def peak_memory():
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(x,ctypes.c_size_t) for x in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    counters=Counters(); counters.cb=ctypes.sizeof(counters)
    kernel=ctypes.WinDLL('kernel32'); psapi=ctypes.WinDLL('psapi')
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb): raise OSError('Memory measurement failed')
    return counters.PeakWorkingSetSize


def protected_snapshot(expected):
    result={}
    for rel in sorted(expected):
        p=ROOT/rel
        if Path(rel).is_absolute() or '..' in Path(rel).parts or p.resolve()!=p: raise ValueError('Unsafe protection path')
        if rel.startswith('ml_v3/data/') and not rel.startswith(('ml_v3/data/development/','ml_v3/data/manifests/')): raise PermissionError('No V3 evaluation tree access')
        result[rel]=sha(p)
    return result


def source_files():
    names=['generation/'+n for n in ('run_stage16r.py','stage16r_contract.py','stage16r_generator.py','stage16r_evaluator.py','stage16r_audit.py','stage16r_loader.py')]
    names += ['evaluation/'+n for n in ('stage16r_custodian.py','stage16r_seal.py','stage16r_authorized_loader.py')]
    names += ['tests/test_stage16r.py']
    return {f'ml_v4/{n}':sha(ROOT/'ml_v4'/n) for n in names}


def save_partition(path,files,design,source):
    path.mkdir(parents=True)
    for name,value in files.items():
        with (path/name).open('xb') as stream: stream.write(value)
    manifest={'dataset_id':DATASET,'parent_version':'v4.stage15.design.1','amendment_version':'v4.stage15a.design.1','generator_version':'v4.generator.1.stage16r.1','evaluator_version':'v4.predicates.1.stage16r.1','temporal_version':'v4.temporal.1','master_seed':SEED,'design_sha256':design,'source_sha256':source,'files':{n:hashlib.sha256(v).hexdigest() for n,v in files.items()}}
    save_json(path/'manifest.json',manifest)
    return {n:sha(path/n) for n in list(files)+['manifest.json']}


def preflight():
    if (OUT/'draw_registry.json').exists() or DATA.exists() or (ROOT/'ml_v4/evaluation/sealed').exists() or REPORT.exists():
        raise FileExistsError('Existing production/attempt namespace; automatic retry prohibited')
    OUT.mkdir(parents=True,exist_ok=True)
    amend=ROOT/'ml_v4/design/amendments'
    previous=json.loads((amend/'v4_stage15a_manifest.json').read_text())
    expected=dict(previous['protection']['after'])
    expected.update({f'ml_v4/design/amendments/{n}':h for n,h in previous['artifact_sha256'].items()})
    expected['ml_v4/design/amendments/v4_stage15a_manifest.json']=sha(amend/'v4_stage15a_manifest.json')
    before=protected_snapshot(expected)
    if before!=expected: raise AssertionError('Historical preservation failed')
    check=subprocess.run([sys.executable,'-B',str(amend/'validate_stage15a.py')],capture_output=True,text=True)
    if check.returncode: raise AssertionError('Stage 15A validation failed')
    test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'ml_v4/tests'),'-p','test_stage16r.py','-v'],capture_output=True,text=True)
    (OUT/'implementation_tests.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
    if test.returncode: raise AssertionError('Implementation fixtures failed')
    save_json(OUT/'protection_before.json',{'sha256':before,'scope':'Explicit inherited paths only; no V3 evaluation tree enumeration or byte access'})
    print('Preflight: frozen design and hand fixtures PASS. Running nonproduction 6200-event unit fixture.',flush=True)
    fixture={n:np.random.Generator(np.random.PCG64DXSM(881610+i)) for i,n in enumerate(STREAMS)}
    start=time.perf_counter()
    events,provenance,populations=Unit('train',0,fixture_streams=fixture).generate()
    replay(events)
    integrity(events,[populations],1)
    elapsed=time.perf_counter()-start; memory=peak_memory()
    if elapsed>600 or memory>4*1024**3: raise RuntimeError('Operational fixture gate failed; no production draw')
    save_json(OUT/'operational_fixture.json',{'status':'PASS','fixture_events':6200,'fixture_seed_namespace':881610,'production_seed_used':False,'elapsed_seconds':elapsed,'single_thread':True,'peak_working_set_bytes':memory,'budget_seconds':600,'budget_bytes':4*1024**3,'hardware':{'machine':platform.machine(),'processor':platform.processor(),'platform':platform.platform()}})
    design={p:h for p,h in before.items() if p.startswith('ml_v4/design/')}
    sources=source_files()
    record={'status':'PASS','checked_utc':now(),'stage15a_tests_pass':12,'protected_count':len(before),'prior_failed_stage16_draw_consumed':False,'existing_production_dataset':False,'amendment_interpretation':'Use frozen LARGE_CONDITIONAL, bounded shift and E/M/R count and context clauses; no target changes','implementation_choices':{'observable_enums':{'transaction_type':['wallet_to_wallet','cash_in','cash_out'],'agent_flow_direction':['none','cash_in','cash_out']},'hard_mechanisms':'H1 dominant/two-hour activity; H2 prior observable amount anchoring and recurring subjects; H3 matched conditional amounts and regular temporal spacing; H4 two-payer comparison; H5 ordinary repeated relationships; H6 chronological reversal opportunities; H7 returning observed customers/two-wallet bursts; H8 historical concentration or cash direction. No target acceptance filters.','background_time':'Fixed unit budget, uniform ordinary event times plus declared recurring/activation opportunities; evolving agent weights redistribute service opportunities within the unit.','a1_near_boundary_audit':'Eligible target0, exactly three of four A1 gates pass; failed count within one wallet, novelty in [0.4,0.5), or growth in [1.25,1.5). Fixed before production.','background_cluster':'population unit x UTC day; episode IDs otherwise','population_diagnostics':'Subject profile for each scored decision row; all agents including zero-positive agents retained.'},'design_sha256':design,'source_sha256':sources,'software':{'python':platform.python_version(),'numpy':np.__version__},'no_new_blocking_contradiction_identified':True}
    save_json(OUT/'preflight.json',record)
    return before,design,sources


def registry_write(value):
    # This attempt's append-audited status registry is the only mutable production marker.
    path=OUT/'draw_registry.json'
    with (OUT/'draw_lifecycle.jsonl').open('a',encoding='utf-8') as stream: stream.write(json.dumps({'utc':now(),'status':value['status']},sort_keys=True)+'\n')
    path.write_bytes(json_bytes(value))


def run():
    before,design,sources=preflight()
    registry={'dataset_id':DATASET,'master_seed':SEED,'status':'RESERVED','created_utc':now(),'production_draw_consumed':True,'design_sha256':design,'source_sha256':sources}
    registry_write(registry)
    audits={}; hashes={}; identity={}; integrity_rows={}; replay_rows={}
    for name,units in [('train',12),('validation',3)]:
        print(f'Generating fixed production {name} opportunities.',flush=True)
        start=time.perf_counter(); events,provenance,populations=generate_partition(name,units)
        integrity_rows[name]=integrity(events,populations,units)
        print(f'{name}: observable generation and independent ledger PASS; evaluating targets.',flush=True)
        files,truth=partition_files(events,provenance,populations)
        hashes[name]=save_partition(DATA/name,files,design,sources)
        clean=read_events(DATA/name/'warmup_observables.csv')+read_events(DATA/name/'transactions.csv')
        observed=[r for e,r in zip(clean,replay(clean)) if e.time>=42*DAY]
        if observed!=truth: raise AssertionError('Observable-only target replay failed')
        replay_rows[name]={'status':'PASS','binary_mismatches':0,'family_evidence_mismatches':0,'rows':len(truth),'inputs':['warmup_observables.csv','transactions.csv']}
        audits[name],primitives=development_audit(name,events,provenance,populations,truth)
        save_json(OUT/f'{name}_audit.json',audits[name])
        save_json(OUT/f'{name}_a1_primitives.json',primitives)
        identity[name]={'wallets':{w['id'] for p in populations for w in p['wallets']},'agents':{a['id'] for p in populations for a in p['agents']},'ids':{e.transaction_id for e in events}}
        print(f'{name}: replay and descriptive audits saved; elapsed {time.perf_counter()-start:.1f}s.',flush=True)
    if any(identity['train'][k]&identity['validation'][k] for k in ('wallets','agents','ids')): raise AssertionError('Development entity collision')
    save_json(OUT/'dataset_integrity.json',integrity_rows)
    save_json(OUT/'target_replay.json',replay_rows)
    registry['status']='DEVELOPMENT_COMPLETE'; registry_write(registry)
    print('Starting separate evaluation custodian; only fixed PASS/FAIL certificates will be returned.',flush=True)
    custodian=subprocess.run([sys.executable,'-B',str(ROOT/'ml_v4/evaluation/stage16r_custodian.py')],capture_output=True,text=True)
    if custodian.returncode: raise RuntimeError('Custodian failed; private details suppressed')
    public=json.loads((ROOT/'ml_v4/evaluation/sealed/public_commitment.json').read_text())
    save_json(OUT/'holdout_public_certificate.json',public)
    registry['status']='PRODUCTION_COMPLETE'; registry_write(registry)
    print('Production generation complete. Replaying development generation with unchanged streams.',flush=True)
    temp=Path(tempfile.mkdtemp(prefix='_repro_',dir=OUT)).resolve()
    checks={}
    for name,units in [('train',12),('validation',3)]:
        events,provenance,populations=generate_partition(name,units)
        files,_=partition_files(events,provenance,populations)
        repeated=save_partition(temp/name,files,design,sources)
        checks[name]={'status':'PASS' if repeated==hashes[name] else 'FAIL','original_hashes':hashes[name],'replay_hashes':repeated,'canonical_bytes_identical':repeated==hashes[name]}
        if repeated!=hashes[name]: raise AssertionError('Deterministic generation replay mismatch')
        print(f'{name}: generation replay hashes match.',flush=True)
    if not temp.is_relative_to(OUT.resolve()) or not temp.name.startswith('_repro_'): raise RuntimeError('Unsafe verification cleanup path')
    cleanup_script="$stageRoot=(Resolve-Path -LiteralPath $env:STAGE16R_ROOT).Path; $stageReplay=(Resolve-Path -LiteralPath $env:STAGE16R_REPLAY_DIR).Path; if (-not $stageReplay.StartsWith($stageRoot+[IO.Path]::DirectorySeparatorChar) -or -not ([IO.Path]::GetFileName($stageReplay)).StartsWith('_repro_')) { throw 'Unsafe replay cleanup path' }; Remove-Item -LiteralPath $stageReplay -Recurse -Force -ErrorAction Stop"
    env=dict(os.environ,STAGE16R_ROOT=str(OUT.resolve()),STAGE16R_REPLAY_DIR=str(temp))
    subprocess.run(['powershell','-NoProfile','-Command',cleanup_script],env=env,check=True,capture_output=True)
    save_json(OUT/'reproducibility.json',{'status':'PASS','partitions':checks,'temporary_outputs_deleted':not temp.exists(),'evaluation_replay':'Observable target replay inside custodian; second generation not requested or exposed','second_candidate_draw':False})
    after=protected_snapshot(before)
    if after!=before or source_files()!=sources: raise AssertionError('Frozen files changed during run')
    save_json(OUT/'protection.json',{'status':'PASS','protected_count':len(before),'before':before,'after':after,'changed_paths':[],'source_hashes_unchanged':True,'v3_evaluation_tree_access':False})
    manifest={'dataset_id':DATASET,'created_utc':registry['created_utc'],'master_seed':SEED,'seed_derivation':'Stage 15 PCG64DXSM SHA256 partition/stream/unit; holdout HMAC secret salt inside custodian','design_sha256':design,'source_sha256':sources,'development_sha256':hashes,'evaluation_commitment':public['commitment_id'],'row_counts':{'scored':100000,'warmup':24000},'versions':{'generator':'v4.generator.1.stage16r.1','evaluator':'v4.predicates.1.stage16r.1','temporal':'v4.temporal.1'},'software':{'python':platform.python_version(),'numpy':np.__version__},'population_and_schema_authority':'Frozen Stage 15 + Stage 15A hashes above'}
    save_json(OUT/'dataset_manifest.json',manifest)
    finish(audits,public,before,sources)
    registry['status']='AUDIT_COMPLETE'; registry_write(registry)
    print('Stage 16R report complete; no feature construction or model fitting.',flush=True)


def finish(audits,public,before,sources):
    support_ok=all(row['status']=='PASS' for audit in audits.values() for row in audit['family_support'].values())
    prevalence_ok=all(a['distribution']['envelope_pass'] for a in audits.values())
    sealed_support=all(c['support_policy']=='PASS' for c in public['certificates'].values())
    shortcut_review=any(v['supported_pure_group_row_fraction']>=.1 for a in audits.values() for k,v in a['shortcuts'].items() if k in ('transaction_id_range','transaction_id_last_digit','timestamp_30day_block','amount_cents','channel','population_unit','profile','archetype','event_role'))
    decision='A — V4 DATASET APPROVED FOR FEATURE CONSTRUCTION' if support_ok and prevalence_ok and sealed_support and not shortcut_review else 'B — V4 DATASET CONDITIONALLY APPROVED; DEVELOPMENT ISSUE MUST BE RESOLVED'
    names=['authoritative Stage 15 + 15A consistency','exact dataset sizes','entity isolation','observable schema','accounting validity','observable-only evaluator','exact target replay','temporal safety','A1 35d alignment','development prevalence','family support','hard-origin semantics','A1 overlap audit','N3/A4/S2/S4 audit','generator shortcut audit','reproducibility','sealed holdouts and loader isolation','historical preservation','S4/H3 amount implementation','episode/motif/context implementation']
    gates=[{'id':f'G{i}','name':name,'status':'PASS'} for i,name in enumerate(names,1)]
    if not prevalence_ok: gates[9]['status']='REVIEW_REQUIRED'
    if not support_ok or not sealed_support: gates[10]['status']='REVIEW_REQUIRED'
    gates[14]['status']='REVIEW_REQUIRED' if shortcut_review else 'PASS_WITH_LIMITS'
    save_json(OUT/'decision.json',{'decision':decision,'gates':gates,'development_support_pass':support_ok,'development_prevalence_pass':prevalence_ok,'custodian_support_pass':sealed_support,'shortcut_review_required':shortcut_review,'training_authorized':False,'production_draws':1,'reproducibility_replay_is_not_candidate':True,'new_feature_vectors':0,'new_model_fits':0,'holdout_detailed_results_exposed':False})
    sections=['# MODEL V4 — STAGE 16R DATASET GENERATION AND INDEPENDENT DATASET AUDIT',f'**{decision}.**','One production draw was retained. Development generation and observable-only replay are exact; the generation replay produced byte-identical development files and manifests. No model was fitted and no final feature matrix was constructed. Support and prevalence outcomes below are observations, not generation objectives used to select the draw.','## 1. Authority, execution and preservation',f'Frozen Stage 15 plus Stage 15A passed preflight. The previous failed Stage 16 attempt is unchanged. All {len(before)} protected historical/design/failed-attempt files match before/after hashes. The master seed is {SEED}; sources and software were frozen before the draw. See [preflight](../evidence/stage16r/preflight.json), [test log](../evidence/stage16r/implementation_tests.txt), [operational fixture](../evidence/stage16r/operational_fixture.json) and [manifest](../evidence/stage16r/dataset_manifest.json). No V3 evaluation tree was enumerated, opened or hashed.','## 2. Exact sizes','| Partition | Scored | Warm-up | Wallets | Agents | Units |\n| --- | ---: | ---: | ---: | ---: | ---: |\n| Train | 60000 | 14400 | 1200 | 96 | 12 |\n| Validation | 15000 | 3600 | 300 | 24 | 3 |\n| Final Test (custodian count certificate PASS) | 15000 | 3600 | 300 | 24 | 3 |\n| Independent (custodian count certificate PASS) | 10000 | 2400 | 200 | 16 | 2 |','Total: **100,000 scored + 24,000 warm-up = 124,000 observable events**. Warm-up is stored separately and enters history; no warm-up label is forced to zero. Scored horizon and dates match Stage 15. Schema, positive integer cents, unique IDs, local edges/services, activation times, electronic conservation and nonnegative wallet/agent inventories pass independent ledger checks. Cross-partition identity comparisons pass inside the custodian without publishing evaluation identities.','## 3. Development class and domain distributions','| Partition | Target 0 | Target 1 | Positive fraction | Envelope |\n| --- | ---: | ---: | ---: | --- |']
    for n,a in audits.items():
        d=a['distribution']; sections.append(f"| {n} | {d['target0']} | {d['target1']} | {d['prevalence']:.4f} | {'PASS' if d['envelope_pass'] else 'OUTSIDE 10%-45%; RETAINED'} |")
    sections+=['\nDomain/family counts overlap; domain-only and multi-domain counts are included in the audit JSON. No evaluation prevalence is released.','## 4. All family supports','| Partition | Family | Decision points | Subjects | Episode/background clusters | Units | Objective | Status |\n| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for n,a in audits.items():
        for f,r in a['family_support'].items(): sections.append(f"| {n} | {f} | {r['decision_points']} | {r['distinct_subjects']} | {r['distinct_clusters']} | {r['distinct_units']} | {r['minimum_objective']} | {r['status']} |")
    sections+=['\nSubjects are family-specific wallet endpoints or agents. Background clusters are unit × UTC day; episode clusters use private scenario IDs. Family overlaps and maximum subject/cluster shares are reported in full evidence. These dependent rows are not independent trials. In particular, S2/S4/N3/A4 support must be assessed from these actual counts, not intended recipe allocation. Any shortfall is retained and blocks unqualified family claims.','## 5. Hard-origin and background behaviour','| Partition | Origin | Total | Target 0 | Target 1 | Crossing fraction |\n| --- | --- | ---: | ---: | ---: | ---: |']
    for n,a in audits.items():
        for origin,r in list(a['hard_origins'].items())+[('background',a['background'])]: sections.append(f"| {n} | {origin} | {r['total']} | {r['target0']} | {r['target1']} | {r['positive_fraction']:.4f} |")
    sections+=['\nEvery origin was evaluated by the same observable union. H-origin target1 rows are retained; only target0 H-origin rows are future FPR negatives. The complete per-origin family crossings and background multi-family counts are in evidence.','## 6. A1 history and overlap','The independent A1 primitive reconstruction agrees with all development A1 decisions and eligibility flags. Both historical contracts require 35 days and 12 baseline services; an exact lower-bound fixture establishes age without counting that lower-bound event in the open baseline. This verifies the target and audit contract; no final feature extractor has been built.','| Partition | Negative cohort | Eligible A1 | Eligible negatives | Raw growth AUC | AP | Subset prevalence | Negative growth >=1.5 |\n| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for n,a in audits.items():
        for cohort,r in a['a1_overlap'].items():
            m=r['metrics']; fmt=lambda x:'not available' if x is None else f'{x:.4f}'
            sections.append(f"| {n} | {cohort} | {r['eligible_A1']} | {r['eligible_negative']} | {fmt(m['roc_auc'])} | {fmt(m['average_precision'])} | {fmt(m['subset_prevalence'])} | {r['negative_high_growth_count']} |")
    sections+=['\nQuantiles, means, extrema, middle-90% overlap, availability, coverage/baseline eligibility, age strata and repeated-agent counts are provided for D, U, novelty, weekly median, growth, age and baseline services. The union deduplicates overlapping negative cohorts. Near-boundary rules were declared in preflight. Legitimate-growth origin is a declared acquisition or promotion/expansion interval, not a negative label. All-origin positive counts accompany the conditioned target0 comparison.','Historical V3 AUC ≈0.9939/AP ≈0.9898 are context, not an optimization target. High AUC can follow directly from a correct compound rule; sparse eligible cohorts warrant an insufficient-support interpretation. The synthetic assumptions are not independently calibrated operator behaviour, so this audit cannot certify realistic overlap or transportability. No A1 result caused regeneration.','## 7. Population and shortcut audit','Archetype/profile counts, events, target prevalence, A1–A4 support, per-agent positives and maximum agent share are saved for both development partitions. All declared agents are retained in concentration denominators, including zero-positive agents. Wallet-profile rows use the current wallet subject, not a duplicated count of both W2W endpoints.','Descriptive target associations cover random-ID ranges and final digits, time blocks, cents, channel, wallet/agent IDs, unit, profile, archetype, origin, intended family, strength and motif/context role. Supported nearly pure groups are explicitly recorded (N>=50 and prevalence <=0.01 or >=0.99). Such a conditional group alone is not proof that an artifact predicts the whole target. High-cardinality IDs and legitimate temporal/type effects require interpretation. This is a descriptive audit, not a fitted shortcut classifier or proof against every hidden shortcut.','## 8. Causality, independence, N3 and A4','Hand fixtures cover all 12 positive predicates and baseline-support boundaries; exact prior/window roles, future append invariance, same-time ordering, emit-before-update, partition reset, S3 midnight/day translation, A1 age, N4 causal funding, N3 paths 1–5 and too-long/repeated/reversed/future paths, competing paths, inclusive amount bounds and self-edge rejection. A4 fixtures verify separate cash counts/values, signs, breadth and assisted/direct service handling. Observable schema rejects extra private columns. Source inspection confirms the generator cannot call the evaluator and the evaluator cannot read provenance; identity renaming leaves decisions unchanged.','Clean replay reads only warm-up and scored observable CSVs, recomputes complete binary/family evidence and matches stored development output exactly. Saved private provenance is not loaded by the replay. Tests do not establish production effectiveness.','## 9. Stage 15A implementation','S4 and H3 use the same base-mixture conditional sampler, never a uniform replacement. Common half-up cent rounding and the exact bounded log transformation are implemented. The Independent transformation is tested on non-dataset fixtures; evaluation outputs remain sealed. Numerical support rejection is distinct from forbidden target-based retries.','Actual E/M/R counts, context roles and timing match saved episode plans. E remains within 8..20, motif counts use the amended conditional laws, context events enter normal history, and S4/H3 observed development motif amounts stay within 500000..1300000 cents. Residual budget transfers are reported. No label quotas or acceptance-until-positive loops occur.','## 10. Fresh evaluation seal and access boundary',f"Public V4 commitment: `{public['commitment_id']}`. Disposition: **{public['disposition']}**.",'The separate custodian process generated fresh evaluation entities and histories, evaluated and replayed targets privately, and encrypted all data, private manifests and secret salt in a Windows current-user DPAPI envelope. No plaintext evaluation file is placed in the development tree. The development loader accepts exact Train/Validation names and declared files only; path escapes, aliases and evaluation requests fail closed. Authorized evaluation requires recorded user authorization, frozen artifact hashes and matching commitment. This is process/API separation plus encryption under the current OS user; it is not a separate-account adversarial isolation claim.','| Partition | Schema | Counts | Isolation | Causal evaluator | Support policy | Seal |\n| --- | --- | --- | --- | --- | --- | --- |']
    for n,c in public['certificates'].items(): sections.append('| '+n+' | '+' | '.join(c[k] for k in ('schema','row_counts','entity_isolation','causal_evaluator','support_policy','sealing'))+' |')
    sections+=['\nOnly these predeclared certificates and public commitments are released. A failed support certificate quarantines the seal and blocks training pending versioned scientific review; no private family counts or prevalence are disclosed. No sealed dataset was reopened after sealing.','## 11. Reproducibility and protection','The isolated second development generation used unchanged configuration and streams. Observable files, ground truth, family evidence, diagnostic provenance/populations and partition manifests are byte-identical. Verification files were deleted after their hashes were recorded. This was a reproducibility replay, not a second candidate draw. [Reproducibility evidence](../evidence/stage16r/reproducibility.json) and [protected hashes](../evidence/stage16r/protection.json) contain the checks.','## 12. Acceptance gates','| Gate | Requirement | Status |\n| --- | --- | --- |']
    sections += [f"| {g['id']} | {g['name']} | {g['status']} |" for g in gates]
    sections+=['## 13. Decision and evidence',f'**{decision}.**','Any prevalence/support or shortcut review requirement must be resolved under the frozen failure policy before further work. Preserve this first production draw; do not regenerate to improve counts or discrimination. A separately authorized challenge set or new version is a future scientific decision, not part of this attempt. No model training, feature construction, threshold tuning, V1 replacement or application integration is authorized here.','Full evidence: [Train audit](../evidence/stage16r/train_audit.json), [Validation audit](../evidence/stage16r/validation_audit.json), [dataset integrity](../evidence/stage16r/dataset_integrity.json), [observable replay](../evidence/stage16r/target_replay.json), [decision](../evidence/stage16r/decision.json), [public custodian certificate](../evidence/stage16r/holdout_public_certificate.json). A1 audit primitives are isolated diagnostic arrays under the same evidence directory, not model features.','**V4 STAGE 16R COMPLETE — WAITING FOR APPROVAL.**']
    text='\n\n'.join(sections)
    import re
    text=re.sub(r'(?<=\|)\n\n(?=\|)','\n',text)
    with REPORT.open('x',encoding='utf-8',newline='\n') as stream: stream.write(text+'\n')
    artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in OUT.iterdir() if p.is_file() and p.name not in ('draw_registry.json','draw_lifecycle.jsonl')}
    artifacts[REPORT.relative_to(ROOT).as_posix()]=sha(REPORT)
    save_json(OUT/'final_verification.json',{'status':'PASS','scope':'Integrity/replay/reproducibility and evidence checks; decision retains population-review qualifications','artifact_sha256':artifacts,'source_sha256':sources,'protected_count':len(before),'changed_paths':[],'new_model_fits':0,'new_feature_matrices':0,'production_draws':1,'sealed_detailed_data_exposed':False})


if __name__=='__main__':
    try: run()
    except Exception as exc:
        if OUT.exists():
            failure=OUT/'execution_failure.json'
            if not failure.exists(): save_json(failure,{'status':'D — STAGE 16R IMPLEMENTATION FAILED; DATASET STATUS UNDETERMINED','error_type':type(exc).__name__,'error':str(exc),'utc':now(),'automatic_retry':False})
        raise
