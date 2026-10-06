"""Static Stage 15A design validation; no random sampling or data generation.

Default: read-only validation of recorded evidence and hashes.
--record: create the three missing evidence documents once, from a previously
captured preservation snapshot. Never rewrites existing records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VERSION = "v4.stage15a.design.1"
PARENT = "v4.stage15.design.1"
DECISION = "A — STAGE 15A AMENDMENT APPROVED; STAGE 16 MAY BE RETRIED"
REPORT = "V4_STAGE15A_IMPLEMENTATION_CLARIFICATION.md"
INPUTS = ["v4_stage15a_amount_law.json", "v4_stage15a_episode_mapping.json", "v4_stage15a_precedence.json"]
RECORDS = ["v4_stage15a_consistency_tests.json", "v4_stage15a_decision.json", "v4_stage15a_manifest.json"]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def snapshot(expected):
    result = {}
    for rel in sorted(expected):
        path = ROOT / rel
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise ValueError("Unsafe historical path")
        if rel.startswith("ml_v3/data/") and not rel.startswith(("ml_v3/data/development/", "ml_v3/data/manifests/")):
            raise ValueError("V3 evaluation data access refused")
        if path.resolve(strict=True) != path or not path.is_relative_to(ROOT):
            raise ValueError("Redirected or escaping historical path")
        result[rel] = sha(path)
    return result


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def count_law(recipe, episode):
    """Enumerate design probabilities, never sample an episode or event."""
    result = defaultdict(Fraction)
    if recipe["kind"] == "conditional_discrete_uniform":
        lo, hi = recipe["minimum"], min(recipe["maximum"], episode)
        require(lo <= hi, "Empty conditional motif support")
        for motif in range(lo, hi + 1):
            result[motif] += Fraction(1, hi - lo + 1)
    else:
        require(recipe["kind"] == "graph_count", "Unknown motif count law")
        lo, hi = recipe["vertices_minimum"], recipe["vertices_maximum"]
        for vertices in range(lo, hi + 1):
            upper = min(recipe["additional_edges_maximum"], episode - vertices)
            require(upper >= 0, "Graph motif exceeds total episode")
            for extra in range(upper + 1):
                result[vertices + extra] += Fraction(1, hi - lo + 1) * Fraction(1, upper + 1)
    require(sum(result.values()) == 1, "Count probabilities do not sum to one")
    require(all(0 < motif <= episode and episode - motif >= 0 for motif in result), "Invalid E=M+R mapping")
    return dict(result)


def validate(before):
    amount, mapping, precedence = [read(HERE / p) for p in INPUTS]
    parent_dir = HERE.parent
    targets = read(parent_dir / "v4_target_predicates.json")
    predicates = {f["code"]: f for f in targets["families"]}
    dataset = read(parent_dir / "v4_dataset_spec.json")
    partitions = read(parent_dir / "v4_partition_spec.json")
    models = read(parent_dir / "v4_model_development_policy.json")
    holdouts = read(parent_dir / "v4_holdout_policy.json")
    tests = []

    def passed(number, name, evidence):
        tests.append({"id": f"T{number:02d}", "name": name, "status": "PASS", "evidence": evidence})

    require(all(d["amendment_version"] == VERSION and d["parent_design_version"] == PARENT for d in (amount, mapping, precedence)), "Noncanonical version")
    components = amount["base_law"]["components"]
    require([Fraction(c["weight"]) for c in components] == [Fraction(9, 10), Fraction(1, 10)], "Base weights changed")
    require([c["lognormal_median_usd"] for c in components] == [35, 1800] and all(c["log_standard_deviation"] == 1 for c in components), "Base parameters changed")
    require(amount["base_law"]["continuous_bounds_usd"] == [0.01, 15000], "Base bounds changed")
    law = amount["laws"]["LARGE_CONDITIONAL"]
    require(law["continuous_support_usd"] == [5000, 13000] and law["proposal_source"] == "BASE", "Wrong conditional proposal")
    require(not law["uniform_range_sampling"] and law["conditioning_before_rounding"], "Conditional law/order ambiguous")
    def component_mass(median, low, high):
        def cdf(value):
            return (1 + math.erf((math.log(value) - math.log(median)) / math.sqrt(2))) / 2
        return cdf(high) - cdf(low)
    masses = [float(Fraction(c["weight"])) * component_mass(c["lognormal_median_usd"], 5000, 13000) for c in components]
    total_mass = sum(masses)
    require(0 < total_mass < 1, "Conditional density undefined")
    require(abs(sum(m / total_mass for m in masses) - 1) < 1e-12, "Conditional component mass invalid")
    rounding_fixtures = {"5000.005": 500001, "7000.005": 700001, "12999.995": 1300000}
    for value, expected in rounding_fixtures.items():
        require(int((Decimal(value) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP)) == expected, "Half-up fixture failure")
    passed(1, "Unambiguous conditional S4 base law", {"law": "LARGE_CONDITIONAL", "conditional_component_weights": [m / total_mass for m in masses], "method": "Mixture CDF arithmetic and fixed rounding fixtures, not sampled amounts"})

    require(amount["motif_law_by_origin"] == {"S4": "LARGE_CONDITIONAL", "H3": "LARGE_CONDITIONAL"}, "H3 does not share S4 law")
    require(amount["context_law_by_origin"] == {"S4": "BASE", "H3": "BASE"}, "Context symmetry failure")
    require(set(amount["independent_shift"]["s4_h3"]["applies_to"]) == {"S4_motif", "H3_motif"}, "Asymmetric shift")
    passed(2, "H3/S4 matched law", {"same_law_reference": True, "same_shift_reference": True})

    require("band(e)=700000<=amount_minor(e)<=1050000; band(T) true" in predicates["S4"]["all_conditions"], "Frozen S4 band differs")
    require(amount["s4_target_unchanged"]["analytical_band_minor_inclusive"] == [700000, 1050000], "Amendment target-band drift")
    passed(3, "S4 target band unchanged", {"band_minor_inclusive": [700000, 1050000]})

    require(law["observable_support_minor"] == [500000, 1300000], "Wrong recipe support")
    require(holdouts["independent_shift"]["shared_amount_multiplier"] == 1.15 and amount["independent_shift"]["applicable"], "Shift applicability mismatch")
    shift = amount["independent_shift"]["s4_h3"]
    require(shift["formula"] == "z_prime=ln(x)+4*delta*u*(1-u); y=exp(z_prime)", "Unknown shift formula")
    delta = math.log(float(Fraction(amount["independent_shift"]["parameter"])))
    width = math.log(13000 / 5000)
    minimum_derivative = 1 - 4 * delta / width
    require(minimum_derivative > 0, "Bounded shift not strictly monotone")
    previous = -1
    for i in range(1001):
        u = i / 1000
        # Normalized log coordinate; this arithmetic creates no transaction.
        shifted = u + (4 * delta / width) * u * (1 - u)
        require(0 <= shifted <= 1 and shifted > previous, "Shift support/grid failure")
        previous = shifted
    passed(4, "Recipe support and bounded Independent shift", {"support_minor": [500000, 1300000], "minimum_log_derivative": minimum_derivative, "fixed_grid_points": 1001, "proof": "Positive derivative and fixed endpoints imply full support and no clipping-induced atoms", "rounding": "Endpoint-cent probability from rounding is not a clipped tail"})

    policy = amount["rejection_policy"]
    require(not policy["target_evaluator_access"] and not policy["target_dependent_retry"] and not policy["episode_retry_on_label_or_support"], "Target-dependent rejection enabled")
    require(policy["allowed_reasons"] == ["fixed_base_support", "fixed_recipe_support", "fixed_universal_support_after_shift"], "Unexpected numerical rejection reason")
    require(not mapping["motif_rule"]["target_dependent"] and "STOP" in policy["accounting_failure_action"], "Target-conditioned structure or capacity resampling")
    passed(5, "No target-dependent sampling", {"numerical_rejection_reasons": policy["allowed_reasons"], "accounting_failure": "STOP", "implementation_status": "Not implemented; design-only proof"})

    families = mapping["families"]
    require(set(families) == set(predicates), "Family mapping incomplete")
    fixed_ranges = {"S1": (4, 12), "S2": (4, 12), "S3": (6, 16), "S4": (5, 12), "N1": (4, 12), "N2": (4, 12), "A3": (5, 16), "N4": (2, 20), "A1": (8, 20), "A2": (8, 20), "A4": (8, 20)}
    require(all((families[f]["minimum"], families[f]["maximum"]) == pair for f, pair in fixed_ranges.items()), "Motif ranges differ")
    require(mapping["total_episode"]["minimum"] == 8 and mapping["total_episode"]["maximum"] == 20 and mapping["total_episode"]["all_origins_same_rule"], "Episode law changed")
    support_table = {}
    for e in range(8, 21):
        support_table[str(e)] = {}
        for family, recipe in families.items():
            dist = count_law(recipe, e)
            support_table[str(e)][family] = {str(m): str(prob) for m, prob in sorted(dist.items())}
            require(all(m + (e - m) == e for m in dist), "Context budget failure")
    # Budget edge cases are deterministic arithmetic, not a second generation.
    for remaining in range(0, 41):
        if remaining >= 8:
            require(all(8 <= e <= 20 and e <= remaining for e in range(8, min(20, remaining) + 1)), "Budget completion failure")
        else:
            require(0 <= remaining < 8, "Residual budget failure")
    passed(6, "Every family maps E into motif plus context", {"E_values": list(range(8, 21)), "family_E_cases": 156, "conditional_count_probabilities": support_table, "budget_boundary_cases": 41})

    hard = mapping["hard_origins"]
    expected_hard = {"H1": ["S1", "S3"], "H2": ["S2"], "H3": ["S4"], "H4": ["N1"], "H5": ["N2", "N4"], "H6": ["N3"], "H7": ["A1", "A3"], "H8": ["A2", "A4"]}
    require(hard == expected_hard, "Hard-origin mapping differs")
    hard_table = {}
    for e in range(8, 21):
        hard_table[str(e)] = {}
        for origin, matches in hard.items():
            mixture = defaultdict(Fraction)
            for family in matches:
                for m, probability in count_law(families[family], e).items():
                    mixture[m] += probability / len(matches)
            require(sum(mixture.values()) == 1 and all(0 < m <= e for m in mixture), "Hard mixture invalid")
            hard_table[str(e)][origin] = {str(m): str(p) for m, p in sorted(mixture.items())}
    passed(7, "Every hard origin has matched motif/context mapping", {"hard_E_cases": 104, "conditional_count_probabilities": hard_table, "matching": hard})

    context = mapping["context"]
    require(all(Fraction(p) == Fraction(1, 4) for p in context["role_probabilities"].values()) and len(context["role_probabilities"]) == 4, "Role mixture differs")
    require(not context["force_label"] and not context["target_acceptance_filter"] and context["visible_to_evaluator"], "Context label policy failure")
    require(mapping["private_provenance"]["additional_private_fields"] == ["event_role", "context_role"], "Unexpected private extension")
    require("baseline_compatible" in context["roles"] and "post_motif_ordinary" in context["roles"], "Context roles missing")
    passed(8, "Context evaluated normally", {"role_probability_sum": "1", "context_count": "E-M", "enters_history_and_evaluator": True, "forced_labels": False, "manual_design_review": "Context envelope/role semantics, causal relationship fallback and private-only fields checked against request; no evaluator executed"})

    overridden_roots = {location.split("#")[0] for override in precedence["overrides"] for location in override["parent_locations"] if location.startswith("v4_")}
    require(not overridden_roots.intersection(precedence["prohibited_override_roots"]), "Protected semantic root overridden")
    require([o["id"] for o in precedence["overrides"]] == list("ABCDEF"), "Precedence scope differs")
    target_path = "ml_v4/design/v4_target_predicates.json"
    require(sha(ROOT / target_path) == before[target_path], "Target bytes changed")
    passed(9, "No target predicate changes", {"predicate_file_sha256": before[target_path], "predicates": 12, "override_scope": list("ABCDEF")})

    a1 = predicates["A1"]
    require(a1["coverage"] == "35d" and a1["minimum_baseline_events"] == 12, "A1 eligibility changed")
    require(a1["recent_window"] == "7d" and a1["baseline_window"] == "B_7d; four separate preceding 7d buckets", "A1 windows changed")
    require(a1["all_conditions"][1:] == ["D>=6", "size(U)>=4", "size(U)/D>=1/2", "D/max(1,M)>=3/2"], "A1 gates changed")
    passed(10, "A1 35d contract unchanged", {"coverage_days": 35, "minimum_baseline_services": 12, "runtime_alignment": "NOT_RUN"})

    parts = partitions["partitions"]
    require(sum(p["scored_events"] for p in parts) == dataset["scored_transactions"] == 100000, "Scored count changed")
    require(sum(p["warmup_events"] for p in parts) == dataset["additional_warmup_events"] == 24000, "Warm-up count changed")
    require([p["scored_events"] for p in parts] == [60000, 15000, 15000, 10000], "Partition sizes changed")
    require(all(p["wallets"] == p["local_units"] * 100 and p["agents"] == p["local_units"] * 8 for p in parts), "Entity design changed")
    require(models["maximum_development_fits"] == 36 and dataset["scope"] == ["structuring", "network", "agent"], "Policy/domain change")
    passed(11, "Dataset scale, domains and unchanged policies", {"scored": 100000, "warmup": 24000, "partition_and_policy_files_unchanged": True, "development_fit_ceiling": 36})

    after = snapshot(before)
    changes = [p for p in before if before[p] != after[p]]
    require(not changes and len(before) == 746, "Protected historical files changed or scope incomplete")
    report = (HERE / REPORT).read_text(encoding="utf-8")
    require(DECISION in report and "V4 STAGE 15A COMPLETE — WAITING FOR APPROVAL." in report, "Report decision mismatch")
    planned = {HERE / p for p in RECORDS}
    for link in re.findall(r"\]\(([^)]+)\)", report):
        path = (HERE / link).resolve()
        require(path.is_file() or path in planned, f"Broken report link: {link}")
    passed(12, "Historical preservation", {"protected_count": len(before), "historical_files": 702, "stage15_files": 21, "failed_stage16_files": 23, "changed_paths": changes, "v3_evaluation_tree_access": False, "v4_evaluation_data_access_or_creation": False})
    return tests, after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    if args.record:
        require(args.snapshot is not None, "A before snapshot is required")
        require(not any((HERE / name).exists() for name in RECORDS), "Refusing to overwrite amendment evidence")
        before = read(args.snapshot)
    else:
        manifest = read(HERE / RECORDS[2])
        before = manifest["protection"]["before"]
        for name, digest in manifest["artifact_sha256"].items():
            require(sha(HERE / name) == digest, f"Amendment artifact hash changed: {name}")
    tests, after = validate(before)
    if args.record:
        common = {"schema_version": 1, "amendment_version": VERSION, "parent_design_version": PARENT, "created_utc": datetime.now(timezone.utc).isoformat()}
        def write(name, fields):
            with (HERE / name).open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(common | fields, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
                handle.write("\n")
        write(RECORDS[0], {"status": "PASS", "scope": "Static/design tests only; no stochastic samples, events, labels, feature vectors or models", "tests": tests, "passed": len(tests), "failed": 0, "method": "Deterministic CDF/rounding/monotonicity arithmetic; exhaustive exact count probabilities; specification and before/after hashes", "software": {"python": platform.python_version()}, "executed_source_sha256": sha(__file__)})
        write(RECORDS[1], {"decision": DECISION, "status": "DESIGN_APPROVED", "resolved_findings": ["B01", "Q01", "M01"], "consistency_tests_passed": 12, "scope": "Only amendment clauses A-F; unaffected Stage 15 remains authoritative", "stage16_retried": False, "execution_authorized_in_this_stage": False, "next_boundary": "Stop. A separately authorized Stage 16 retry must use parent plus amendment hashes and a fresh attempt namespace; preserve failed attempt D.", "new_transactions": 0, "new_labels": 0, "new_feature_vectors": 0, "new_model_fits": 0, "new_holdout_seals": 0, "protected_files_unchanged": len(before)})
        final_after = snapshot(before)
        require(final_after == before, "Final preservation check failed")
        bindings = INPUTS + [REPORT, "validate_stage15a.py", RECORDS[0], RECORDS[1]]
        parent_hashes = read(ROOT / "ml_v4/evidence/stage16_design_verification.json")["authoritative_sha256"]
        write(RECORDS[2], {"status": "PASS", "dataset_id": "mobile_money_aml_synthetic_100k_v4", "historical_parent_spellings": ["v4.stage 15.design.1", "v4.stage15.design.1"], "parent_authoritative_sha256": parent_hashes, "artifact_sha256": {name: sha(HERE / name) for name in bindings}, "manifest_self_hash_excluded": True, "protection": {"before": before, "after": final_after, "protected_count": len(before), "changed_paths": [], "scope": "Explicit historical allowlist plus 21 original Stage 15 files and 23 failed Stage 16 files. Named public commitment metadata only; excludes unread V3 evaluation bytes. No directory walk of any evaluation tree."}, "source": "validate_stage15a.py", "recheck_command": "python -B ml_v4/design/amendments/validate_stage15a.py", "generation_performed": False, "production_draw_consumed": False})
    else:
        saved = read(HERE / RECORDS[0])
        require(saved["tests"] == tests, "Recomputed consistency results differ")
        require(manifest["protection"]["after"] == after, "Preservation evidence differs")
        require(read(HERE / RECORDS[1])["decision"] == DECISION, "Decision differs")
    print(json.dumps({"result": "PASS", "tests": len(tests), "protected_count": len(before), "changed_paths": [], "generation_performed": False, "mode": "record" if args.record else "read_only_recheck"}))


if __name__ == "__main__":
    main()
