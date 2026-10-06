# V3 ground-truth contract — proposed revision 1

Status: Stage 8 design for approval. Dataset identity: `mobile_money_aml_synthetic_100k_v3`. No records, labels, features, or models are created by this document.

## Meaning of the prediction

At the arrival of transaction T, the system asks: **does this transaction make the currently observable wallet, network, or agent state warrant review for a specified suspicious behavioural pattern?** A positive target is a synthetic reference for a review alert. It does not establish money laundering, criminal intent, or a reporting obligation. The research remains a Zimbabwean mobile-money AML decision-support project covering structuring, wallet/network behaviour, and agent behaviour.

Let H(T) contain only records in T's partition whose `(timestamp, transaction_id)` key is strictly smaller than T's. Current observable fields of T are also available. For each family f, evaluate the predicate `C_f(H(T), T)` defined in [the onset contract](V3_SCENARIO_ONSET_CONTRACT.md), on the relevant current wallet/edge/agent. Then:

`decision_point_target(T) = 1 if any C_f(H(T), T) is true; otherwise 0`.

This evaluation covers **every transaction**, including routine events, legitimate hard scenarios, and campaign members. It must not read campaign membership, intended family, strength, future plans, private entity roles, or model predictions. There is no hidden `suspicious_campaign AND predicate` gate.

## Two truth concepts and separate storage

| Field | Meaning | Access/use |
|---|---|---|
| `scenario_member` | Whether the event belongs to a planned suspicious campaign. | Generator metadata and later diagnostic grouping only. |
| `scenario_family`, `campaign_id`, `scenario_strength` | Intended campaign and its sampled behavioural intensity. | Never model inputs or a gate on the decision target. |
| `normal_scenario_family`, `normal_episode_id`, `normal_subtype` | Legitimate scenario provenance, including H1–H8 subtypes. | Diagnostic cohorts; these fields do not force target 0. |
| `decision_point_target` | OR of the 12 observable predicates at T. | The sole supervised binary target. |
| `evidence_families` | All predicates true at T, rather than one forced family. | Evaluation truth only; permits overlap between domains. |
| `evidence_subjects`, `witness_transaction_ids` | Current subject and earlier/current records supporting each satisfied predicate. | Restricted audit ledger, never X. |
| `family_onset_event_id`, `campaign_onset_event_id` | First qualifying relevant trigger for a family/associated campaign; null if none occurs. | Diagnostic metadata determined by chronological evaluation, never a feature. |
| `baseline_eligibility`, `predicate_version` | Audit explanation for an evaluated or ineligible condition. | Truth ledger; independently computed public-history eligibility may be proposed as a feature. |

Observable transaction files contain no truth fields. A separate target table joins by transaction ID. The feature worker receives observable transactions only; a training assembler may subsequently attach targets by verified row ID. Raw IDs are grouping/join keys, never numeric predictors. Planned campaign membership is fixed before materialization; decision targets are computed afterwards by a deterministic chronological reference evaluator.

## Onset, continuation, expiry, and overlapping conditions

The operational family onset is the first event in chronological processing for which that subject's family predicate becomes true following an ineligible/false state. The campaign's diagnostic onset is the first member event at which the intended predicate is true on its current relevant subject. A campaign may never reach onset, or may start while a subject already has qualifying prior activity. Report both cases. Campaign identifiers help describe onset after evaluation; they do not define the history the evaluator sees.

Before a campaign's own onset, its member events receive target 0 **unless a different independently observable predicate is true**. Such cross-family positives must retain their actual evidence-family attribution. After onset, target 1 is not permanent: the current event must be relevant to an active predicate and the predicate must still hold at that event. Window expiry, changing composition, or balancing activity can return it to 0; later reactivation is allowed. No campaign-wide or subject-wide target latch is permitted.

N3 is a closure-event predicate: earlier open-path edges remain 0 for N3, and a later unrelated edge does not inherit a previous closure. N4 applies to current outflows/exits meeting the funding condition, not to earlier funding/inbound legs. Structuring and agent predicates apply to their current relevant event while their accumulated state satisfies the contract. A balancing cash event may still encounter an imbalanced state; it is positive only if the state including that event still qualifies.

## Legitimate explanations and identical observations

Legitimate purpose is not a permission to contradict observable truth. A legitimate H6 refund that meets the exact N3 condition is target 1 for review, even though its private narrative is lawful. It remains in the legitimate-origin cohort. A hard-negative event is, strictly, an event from that cohort whose decision target is 0. Report both review rates over the full legitimate cohort and false positives among its target-0 members.

If two observations have identical permitted histories and current fields, their targets must match. An ambiguity flag can document that illicit intent is unknowable; it cannot flip the target. Causal differences needed for a legitimate example to remain target 0 must exist in the observable history. No invented merchant-status, risk, or exemption field may reveal a private narrative.

## Independence and limits of a synthetic oracle

The onset constants are reference-truth assumptions, not application rules and not conclusions about Zimbabwean law. They are fixed before generation and before model results. The reference evaluator and feature implementation must be separate modules, with independent implementations and hand-worked checks. The feature worker must not import the evaluator or receive predicate bits, onset position, thresholds-as-label encodings, or completed-episode statistics.

Statistical dependence between causal features and this rule-generated target is intentional and unavoidable. This experiment tests whether a compact representation approximates a synthetic behavioural reference. It cannot validate the reference itself or establish effectiveness on real illicit activity. Independent expert assessment or real-world validation would be required for those claims. Exact oracle reconstruction must be reported as synthetic rule approximation, not discovery of money laundering.

## Required correctness checks before a future generation is accepted

1. Prefix invariance: evaluating T on a prefix and on the complete stream gives the same target and witnesses. Changing future transactions cannot change earlier labels.
2. Metadata invariance: changing/removing campaign IDs, intended family, strength, and legitimate narrative leaves targets unchanged for fixed observable records.
3. Current-event inclusion: a closing cycle edge or qualifying outflow may trigger now; it cannot retroactively label earlier edges.
4. Permuting input rows and then restoring canonical order leaves the output unchanged. Duplicate IDs, invalid times, cross-partition edges, and ambiguous serviced-wallet assignments are rejected.
5. All positive witnesses have keys no later than T, match its permitted partition and subject, and satisfy exact window and amount semantics.
6. Onset-free campaigns, pre-onset target-0 events, post-onset target-0 events, cross-family positives, and legitimate-origin positives are retained and counted.

These are acceptance checks for a future authorized implementation. No target is chosen, removed, or altered to improve a classifier score.
