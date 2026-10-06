# MODEL V3 — STAGE 9 GROUND-TRUTH AUDIT

Ground truth is `decision_point_target = 1` exactly when at least one of the 12 universal predicates qualifies at the current decision point. The evaluator records `evidence_families`, `evidence_subjects`, witness transaction IDs and onset references. It never reads future rows, scenario membership, origin cohort or generator provenance when deciding the target.

The generated target totals are:

| Partition | Target 0 | Target 1 |
|---|---:|---:|
| Train | 39,781 | 20,219 |
| Validation | 9,945 | 5,055 |
| Final Test | 10,062 | 4,938 |
| Independent | 7,134 | 2,866 |

Campaign membership and hard-origin status are diagnostic dimensions. Routine rows can receive a target when observable history satisfies a predicate, and campaign rows can remain negative before a motif becomes observable. This is intentional decision-point ground truth. Predicate version: `v3_onset_contract_rev1`.

The complete machine-readable breakdown is in [`V3_STAGE9_GENERATION.json`](V3_STAGE9_GENERATION.json); the evaluator implementation is [`reference_evaluator.py`](../src/reference_evaluator.py).
