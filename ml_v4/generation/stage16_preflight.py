"""Record the frozen Stage 15 preflight failure. Does not generate any events.

This is a report writer for the inspected design revision, not a generator or
an approval gate for a future amended design. Refuses changed inputs/outputs.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "ml_v4/design"
EVIDENCE = ROOT / "ml_v4/evidence"
REPORT = ROOT / "ml_v4/reports/V4_STAGE16_DATASET_GENERATION_AUDIT.md"
NAMES = (
    "dataset_spec temporal_contract target_predicates target_feature_alignment "
    "feature_spec agent_population_spec wallet_population_spec hard_negative_spec "
    "family_support_policy partition_spec holdout_policy model_development_policy "
    "evaluation_metrics generator_audit_plan acceptance_gates v3_comparison "
    "reproducibility_spec stage15_decision"
).split()
AUDITS = (
    "dataset_integrity entity_isolation temporal_safety target_independence "
    "target_replay development_distribution family_support hard_origin_audit "
    "background_audit a1_overlap_audit agent_population_audit wallet_population_audit "
    "n3_audit a4_audit structuring_support_audit shortcut_audit reproducibility"
).split()
DECISION = "D — STAGE 16 IMPLEMENTATION FAILED; DATASET STATUS UNDETERMINED"


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot(paths):
    result = {}
    for rel in sorted(paths):
        # Only explicit historical allowlist entries; never walk a data tree.
        p = Path(rel)
        if p.is_absolute() or ".." in p.parts:
            raise ValueError(f"Unsafe protection path: {rel}")
        if rel.startswith("ml_v3/data/") and not rel.startswith(
            ("ml_v3/data/development/", "ml_v3/data/manifests/")
        ):
            raise ValueError("V3 non-development data access refused")
        resolved = (ROOT / p).resolve(strict=True)
        if not resolved.is_relative_to(ROOT):
            raise ValueError("Protection path escapes workspace")
        if resolved != ROOT / p:
            raise ValueError("Protection path redirection refused")
        result[rel] = sha(resolved)
    return result


def main():
    files = [DESIGN / f"v4_{name}.json" for name in NAMES]
    files += [DESIGN / "V4_STAGE15_CONTROLLED_REDESIGN_SPECIFICATION.md"]
    frozen_verification = read(DESIGN / "v4_stage15_verification.json")
    hashes = {p.name: sha(p) for p in files}
    for name, digest in hashes.items():
        if frozen_verification["artifact_sha256"][name] != digest:
            raise RuntimeError(f"Frozen input changed: {name}; review anew")
    docs = {n: read(DESIGN / f"v4_{n}.json") for n in NAMES}
    historical = read(DESIGN / "v4_stage15_protection.json")
    protected = dict(historical["after"])
    for p in files + [DESIGN / "v4_stage15_protection.json", DESIGN / "v4_stage15_verification.json"]:
        protected[p.relative_to(ROOT).as_posix()] = sha(p)
    before = snapshot(protected)
    if before != protected:
        raise RuntimeError("Protected input changed since Stage 15")

    outputs = [EVIDENCE / f"stage16_{n}.json" for n in AUDITS + [
        "design_verification", "protection", "decision", "final_verification"
    ]] + [REPORT]
    if any(p.exists() for p in outputs):
        raise FileExistsError("Stage 16 outputs already exist; preserve this attempt")

    predicates = {f["code"]: f for f in docs["target_predicates"]["families"]}
    features = {f["name"]: f for f in docs["feature_spec"]["features"]}
    alignments = {f["family"]: f for f in docs["target_feature_alignment"]["families"]}
    partitions = docs["partition_spec"]["partitions"]
    temporal = docs["partition_spec"]["temporal"]
    checks = {
        "all_19_authoritative_files_present_and_hash_match_stage15": True,
        "stage15_decision_is_A": docs["stage15_decision"]["decision"] == "A — V4 DESIGN APPROVED FOR GENERATION",
        "12_unique_predicates": len(predicates) == 12,
        "40_unique_features": len(features) == 40,
        "12_alignment_rows": set(alignments) == set(predicates),
        "100000_scored_design_total": sum(p["scored_events"] for p in partitions) == 100000,
        "24000_warmup_design_total": sum(p["warmup_events"] for p in partitions) == 24000,
        "unit_arithmetic": all(p["wallets"] == p["local_units"] * 100 and p["agents"] == p["local_units"] * 8 and p["scored_events"] == p["local_units"] * 5000 and p["warmup_events"] == p["local_units"] * 1200 for p in partitions),
        "42_day_warmup": (datetime.fromisoformat(temporal["scored_start"]) - datetime.fromisoformat(temporal["start"])).days == 42,
        "180_day_scored_horizon": (datetime.fromisoformat(temporal["scored_end_exclusive"]) - datetime.fromisoformat(temporal["scored_start"])).days == 180,
        "master_seed": docs["reproducibility_spec"]["proposed_master_seed"] == 2026092915,
        "feature_history_cross_references": all(
            entry["window"] == features[entry["name"]]["window"]
            and entry["eligibility"] == features[entry["name"]]["eligibility"]
            for a in alignments.values() for entry in a["feature_history"]
        ),
        "predicate_alignment_cross_references": all(
            a["target_recent"] == predicates[n]["recent_window"]
            and a["target_baseline"] == predicates[n]["baseline_window"]
            and a["target_coverage"] == predicates[n]["coverage"]
            and a["minimum_events"] == predicates[n]["minimum_baseline_events"]
            and a["minimum_distinct"] == predicates[n]["minimum_baseline_distinct"]
            for n, a in alignments.items()
        ),
        "A1_design_35d_and_12_baseline_services": predicates["A1"]["coverage"] == "35d" and predicates["A1"]["minimum_baseline_events"] == 12 and all(
            "35d" in features[n]["eligibility"] and ">=12 baseline services" in features[n]["eligibility"]
            for n in ("agent_wallet_growth_ratio_7d", "agent_new_wallet_count_7d", "agent_new_wallet_share_7d")
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Unexpected additional structural failure: {checks}")

    support = docs["family_support_policy"]
    findings = [
        {
            "id": "B01", "severity": "BLOCKING", "classification": "Unresolved amount-law conflict",
            "sources": ["v4_dataset_spec.json#/amount_process", "v4_family_support_policy.json#/family_recipe_design/S4", "report sections 18 and 22"],
            "clauses": [docs["dataset_spec"]["amount_process"], support["family_recipe_design"]["S4"]],
            "reason": "The shared mixture for all recipe origins has support below USD 5000 and above USD 13000, whereas S4 recipe amounts are confined to USD 5000..13000. The permission for recipe-specific amount relations does not specify whether this absolute range conditions the mixture or replaces it, nor define a replacement density. Both choices affect opportunity support and shortcuts. Common cent rounding does not settle the amount law.",
            "not_inferred": "Continuous does not imply uniform. No uniform S4 distribution is assumed here.",
            "required_resolution": "Version an explicit precedence and sampling rule for S4 and its matched H3 mechanism, including whether the shared mixture is conditioned on the range, how Independent scaling/bounds apply, and which rounding/jitter rules are shared. Keep existing Stage 15 bytes unchanged.",
        },
        {
            "id": "Q01", "severity": "CLARIFICATION_REQUIRED", "classification": "Episode versus motif size is not resolved",
            "sources": ["v4_family_support_policy.json#/opportunity_recipe", "v4_family_support_policy.json#/family_recipe_design", "report section 22"],
            "clauses": [support["opportunity_recipe"], support["family_recipe_design"]["S1"], support["family_recipe_design"]["S3"], support["family_recipe_design"]["A3"]],
            "reason": "The common episode law assigns 8..20 events, while named recipes specify 4..12, 6..16 or 5..16 events/services. Preparatory/pre-onset events are allowed in the budget, so this need not be a mathematical contradiction. However, the mapping of a 20-event episode to a maximum-12-event motif, and a maximum-16-event motif to an 8-event episode, is unspecified. Silently truncating, splitting, padding or overriding a range changes the population law.",
            "required_resolution": "State whether recipe counts describe a motif within the full episode; define count sampling conditional on the episode budget and the roles, timing, amounts and provenance of remaining events, with matched hard-origin treatment.",
        },
        {
            "id": "M01", "severity": "NONBLOCKING_METADATA", "classification": "Design-version spelling differs in evidence",
            "sources": ["v4_stage15_verification.json#/design_version", "v4_dataset_spec.json#/design_version"],
            "values": [frozen_verification["design_version"], docs["dataset_spec"]["design_version"]],
            "reason": "The authoritative JSON specs consistently use the spaced version string; auxiliary Stage 15 verification uses the unspaced spelling. Exact content hashes still identify the inspected artifacts. This is not the generation stop reason.",
        },
    ]
    gate_names = [
        "Stage 15 authoritative artifacts consistent", "100000 scored plus 24000 warm-up events",
        "Partition/entity isolation", "Observable schema", "Accounting validity",
        "Observable-only universal evaluator", "Exact observable-only target replay",
        "Temporal safety tests", "A1 target/feature 35d alignment implemented",
        "Development prevalence assessed", "Family support assessed without regeneration",
        "H1-H8 origins, no forced negative labels", "A1 overlap audit",
        "N3/A4/S2/S4 support audits", "Generator shortcut audit", "Dataset reproducibility",
        "Fresh sealed holdouts and loader isolation", "Historical preservation",
    ]
    gates = [{"gate": i, "name": name, "status": "FAIL" if i == 1 else "PASS" if i == 18 else "NOT_RUN", "reason": "B01 unresolved amount-law conflict" if i == 1 else "Explicit before/after protection hashes" if i == 18 else "Generation stopped at Gate 1; no implementation or data audit executed"} for i, name in enumerate(gate_names, 1)]
    now = datetime.now(timezone.utc).isoformat()
    common = {"schema_version": 1, "stage": 16, "attempt": "preflight_only", "created_utc": now, "dataset_id": docs["dataset_spec"]["dataset_id"]}
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    def write(name, obj):
        path = EVIDENCE / f"stage16_{name}.json"
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(common | obj, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            handle.write("\n")

    write("design_verification", {"status": "FAIL", "checks": checks, "findings": findings, "authoritative_sha256": hashes, "authoritative_files": len(files), "mutual_consistency": "FAIL", "review_scope": "Structural cross-checks and generator-contract review; not a certification of all semantics or a working implementation"})
    for name in AUDITS:
        write(name, {"status": "NOT_RUN", "reason": "Stage 16 section 1 stop condition: unresolved frozen design conflict B01", "measurements": None, "rows_generated_this_attempt": 0, "dataset_status": "NOT_GENERATED"})
    after = snapshot(protected)
    changed = [name for name in before if before[name] != after[name]]
    if changed:
        raise RuntimeError(f"Preservation failure: {changed}")
    write("protection", {"status": "PASS", "historical_count": len(historical["after"]), "stage15_count": 21, "protected_count": len(before), "before": before, "after": after, "changed_paths": changed, "v3_holdout_directories_enumerated": False, "v3_holdout_contents_accessed_or_hashed": False, "scope": "702 inherited allowlist paths plus 21 named Stage 15 files; named public V3 commitments are metadata only. No whole-repository or unread holdout-byte claim."})
    write("decision", {"status": "STOPPED_AT_PREFLIGHT", "decision": DECISION, "gates": gates, "blocking_findings": ["B01"], "dataset_status": "UNDETERMINED; NOT_GENERATED", "next_action": "Approve a versioned design amendment resolving B01 and Q01, then rerun implementation preflight. Existing design and this failed attempt remain preserved.", "generation_authorized_by_request": True, "generation_permitted_after_preflight": False, "generated_scored_rows": 0, "generated_warmup_rows": 0, "feature_vectors": 0, "model_fits": 0, "holdout_seals_created": 0})
    report = [
        "# MODEL V4 — STAGE 16 DATASET GENERATION AND INDEPENDENT DATASET AUDIT",
        f"**{DECISION}.**",
        "**Stopped at the mandatory design preflight. No dataset was generated.** The user's Stage 16 section 1 requires STOP when an implementation-blocking contradiction is found and forbids silently reinterpreting Stage 15. This report closes the failed attempt; it does not certify completed generation or dataset audits.",
        "## 1. Authoritative input verification",
        "All 19 required authoritative files exist and match the recorded Stage 15 SHA-256 hashes. The saved Stage 15 decision is A. Counts, dates, 12 predicates, 40 feature declarations and target/feature history references pass structural cross-checks. These checks do not establish generator consistency: Gate 1 fails on B01 below. Exact hashes and source clauses are in [design verification](../evidence/stage16_design_verification.json). Stage 15's previous PASS remains historical evidence and has not been overwritten.",
        "## 2. Blocking amount-law conflict (B01)",
        "[Dataset amount process](../design/v4_dataset_spec.json) (`amount_process`; report section 18) requires the shared 90%/10% lognormal mixture for background and all recipe origins, truncated to USD 0.01..15,000. [S4 opportunity recipe](../design/v4_family_support_policy.json) (`family_recipe_design.S4`; report section 22) confines recipe amounts to USD 5,000..13,000.",
        "The unconditional mixture gives positive probability outside the S4 range. Applying it unchanged violates the S4 recipe. Conditioning it on that range, replacing it with another density, or transforming it would implement different population laws. The permission for recipe-specific amount relations does not choose among these interpretations. The word 'continuous' does not specify a uniform distribution. Shared rounding alone cannot reconcile the amount law.",
        "A versioned amendment must define the precedence, exact S4 sampling law, matched H3 treatment, and interaction with Independent's amount multiplier and bounds. No such amendment was applied in this attempt.",
        "## 3. Additional implementation clarification (Q01)",
        "The common episode size is discrete uniform 8..20, while S1/S2/N1/N2 specify 4..12 events, S4 specifies 5..12, and S3/A3 cap at 16. Preparatory/pre-onset events are explicitly allowed, so these ranges are potentially compatible. The design does not define how motif counts fit a full episode, including an 8-event episode with a larger proposed motif or a 20-event episode with a 12-event motif. Define conditional count sampling and remaining-event roles, timing, values and provenance before implementation; preserve the shared law for matched hard origins. This is reported as an unresolved mapping, not proof that the intervals have no intersection.",
        "Auxiliary Stage 15 evidence spells the design version `v4.stage15.design.1`; authoritative JSON specs use `v4.stage 15.design.1`. Hashes identify the inspected revision. This metadata discrepancy is not the stop reason.",
        "## 4. A1 contract review",
        "The saved target, feature declarations and alignment table agree on 35 days and at least 12 baseline services for A1 growth/newness quantities. Recent distinct-wallet count is deliberately recent-only. **Design alignment: PASS. Runtime alignment: NOT_RUN.** No claim that an implemented evaluator eliminates the V3 mismatch is made.",
        "## 5. Generation and requested empirical results",
        "| Partition | Planned scored | Planned warm-up | Generated scored this attempt | Generated warm-up this attempt |\n| --- | ---: | ---: | ---: | ---: |",
    ]
    for p in partitions:
        report.append(f"| {p['name']} | {p['scored_events']} | {p['warmup_events']} | 0 | 0 |")
    report += [
        "\nPlanned total: 100,000 scored plus 24,000 warm-up. Actual generated total in this attempt: **0**. No random production draw was consumed. No generator, target evaluator, feature extractor or evaluation loader was implemented; the new source records preflight findings only.",
        "| Requested result | Status |\n| --- | --- |\n| Train/Validation class distribution and prevalence | NOT_RUN; unmeasured |\n| All 12 family supports, subjects, clusters and overlap | NOT_RUN; unmeasured |\n| H1–H8 and background actual target states | NOT_RUN; unmeasured |\n| A1 component distributions, growth AUC/AP, legitimate-growth and boundary overlap | NOT_RUN; unmeasured |\n| Agent archetype and wallet profile audits | NOT_RUN; unmeasured |\n| N3, A4, S2 and S4 support and fixtures | NOT_RUN; unmeasured |\n| Shortcut associations | NOT_RUN; unmeasured |\n| Observable-only replay and target independence | NOT_RUN |\n| Temporal safety, schema, accounting and entity isolation | NOT_RUN |\n| Second-generation reproducibility | NOT_RUN |",
        "Unavailable measurements are null in the evidence, not fabricated zero supports or passing tests. V3's A1 AUC 0.9939/AP 0.9898 remain historical context only; there is no V4 result to compare.",
        "## 6. Evaluation status and preservation",
        "V4 Final Test and Independent Evaluation were not generated or sealed. No public V4 commitment, private seed, evaluation manifest or custodian certificate exists from this attempt. Loader isolation is untested. No V3 evaluation tree was enumerated or its contents opened/hashed.",
        f"Before/after hashes match for **{len(before)} protected files**: {len(historical['after'])} inherited historical/application paths and 21 Stage 15 files. Changed paths: `[]`. The claim covers the explicit allowlist, including named public commitment metadata, and excludes unread evaluation bytes. See [preservation evidence](../evidence/stage16_protection.json).",
        "## 7. Acceptance gates",
        "| Gate | Requirement | Result |\n| --- | --- | --- |",
    ]
    report += [f"| {g['gate']} | {g['name']} | {g['status']} |" for g in gates]
    report += [
        "\nGates 2–17 remain unexecuted because Gate 1 stopped generation. Gate 9 has a passing document-level alignment check only. Gate 18 is an executed preservation check. No dataset approval follows from successfully writing this failure report.",
        "## 8. Evidence and reproducibility of the preflight record",
        "All 21 requested JSON evidence artifacts are supplied. The 17 empirical audit artifacts explicitly record NOT_RUN, with null measurements and the stop reason. The remaining four contain design verification, protection, decision and final record verification.",
    ]
    for path in outputs:
        if path.suffix == ".json":
            report.append(f"- [{path.name}](../evidence/{path.name})")
    report += [
        "\nSource: [stage16_preflight.py](../generation/stage16_preflight.py). It uses standard-library document/hash operations, refuses changed frozen inputs and existing output files, and cannot generate data. Final verification hashes the source, report and other evidence; it verifies record consistency only, not dataset reproducibility.",
        "## 9. Required next decision",
        "Approve a separately versioned design amendment defining the S4/H3 amount process and episode-to-motif mapping. Preserve the current Stage 15 files and this failed Stage 16 attempt. A later authorized attempt must first validate the amended design, then implement and pass the required fixtures before consuming the single production draw. The Stage 16 request authorized generation conditionally; its explicit contradiction stop condition is why work stops here.",
        f"**{DECISION}.**",
        "**V4 STAGE 16 COMPLETE — WAITING FOR APPROVAL.**",
    ]
    # Keep table rows adjacent while maintaining blank lines around blocks.
    content = "\n\n".join(report)
    content = re.sub(r"(?<=\|)\n\n(?=\|)", "\n", content)
    content = re.sub(r"(?<=\))\n\n(?=- \[)", "\n", content)
    with REPORT.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content + "\n")
    final_after = snapshot(protected)
    if final_after != before:
        raise RuntimeError("Final protection recheck failed")
    for path in outputs:
        if path.suffix == ".json" and path.name != "stage16_final_verification.json":
            obj = read(path)
            if path.stem.removeprefix("stage16_") in AUDITS:
                assert obj["status"] == "NOT_RUN" and obj["measurements"] is None
    links = re.findall(r"\]\(([^)]+)\)", content)
    assert all((REPORT.parent / link).resolve().is_file() or link.endswith("stage16_final_verification.json") for link in links)
    artifact_paths = [p for p in outputs if p.name != "stage16_final_verification.json"] + [Path(__file__)]
    write("final_verification", {"status": "PASS", "scope": "Preflight failure-record integrity only; Stage 16 execution status remains D", "stage16_execution_status": "STOPPED_AT_PREFLIGHT", "decision": DECISION, "gates": gates, "authoritative_hashes_match_stage15": True, "all_21_evidence_artifacts_accounted_for": True, "protected_count": len(before), "changed_paths": [], "artifact_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in artifact_paths}, "self_hash_excluded": True, "new_data_rows": 0, "new_feature_vectors": 0, "new_model_fits": 0, "new_holdout_seals": 0, "dataset_reproducibility": "NOT_RUN"})
    print(json.dumps({"decision": DECISION, "protected_count": len(before), "changed_paths": [], "authoritative_files": len(files), "evidence_files": 21, "generated_rows": 0}, ensure_ascii=True))


if __name__ == "__main__":
    main()
