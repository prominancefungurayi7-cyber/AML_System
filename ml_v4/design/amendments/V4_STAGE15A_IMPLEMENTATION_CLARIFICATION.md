# MODEL V4 — STAGE 15A CONTROLLED DESIGN AMENDMENT

**A — STAGE 15A AMENDMENT APPROVED; STAGE 16 MAY BE RETRIED.**

Version: `v4.stage15a.design.1`. Canonical parent reference: `v4.stage15.design.1`.

This amendment resolves Stage 16 findings B01 and Q01 and normalizes new metadata. All 12 required static/design consistency tests pass. This is design approval for a separately authorized retry. **No Stage 16 retry or dataset generation was performed.**

## 1. Authority, scope and preservation

The [original Stage 15 design](../V4_STAGE15_CONTROLLED_REDESIGN_SPECIFICATION.md) and [failed Stage 16 report](../../reports/V4_STAGE16_DATASET_GENERATION_AUDIT.md) remain historical artifacts. Stage 16 stopped before consuming a production draw; its decision remains D. This amendment does not retrospectively change that decision.

The [precedence specification](v4_stage15a_precedence.json) overrides Stage 15 only for A–F below. All unaffected clauses retain authority. Exact parent hashes, new artifact hashes, preservation records and version spellings appear in the [manifest](v4_stage15a_manifest.json).

| Clause | Amendment scope |
| --- | --- |
| A | Base amount law and predeclared recipe hierarchy |
| B | S4 conditional amount sampling |
| C | H3 matched sampling and S4/H3 Independent shift interaction |
| D | Total episode size to motif count mapping, including missing count laws |
| E | Context counts, roles, timing and private provenance |
| F | Canonical new metadata and parent reference |

No target predicate, A1 condition, domain, feature declaration, observable schema, partition size, entity allocation, opportunity budget, support objective, accounting capacity, model policy, threshold policy or evaluation metric is changed. Holdout governance is unchanged. The only Independent amount exception is explicitly scoped to S4/H3 motif amounts.

## 2. B01: amount-law hierarchy

The Stage 15 mixture is the **base amount law**. In continuous USD, let

`f(x) = 0.9 LN(x; ln(35), 1) + 0.1 LN(x; ln(1800), 1)`.

BASE is this mixture conditioned on `0.01 <= x <= 15000`. Background, routine, unconstrained recipe events and all context events use BASE directly. Predeclared behavioural recipes may condition or transform proposals, with symmetric treatment of corresponding positive-intended and hard-origin mechanisms where applicable.

The order is:

```text
Base population law
  -> predeclared recipe constraint/transformation
  -> applicable partition amount shift
  -> universal bounds and common cent rounding
  -> accounting feasibility check
  -> observable transaction
```

The target evaluator has no role in sampling, rejection or accounting. Numerical rejection against frozen bounds is allowed. Resampling an event or episode because a predicate did or did not fire is prohibited. An accounting failure stops materialization; it does not trigger amount replacement or unrecorded funding.

Common precision means the same integer-cent grid and rounding rule. It does not require identical cent-frequency histograms after distinct declared behavioural transformations. No new blanket jitter is introduced. Existing S1/S2/N3/N4/A4 amount relations remain inherited.

## 3. Exact S4 and H3 amount law

Both **S4 motif events and H3 motif events use `LARGE_CONDITIONAL`**, defined in the [amount-law specification](v4_stage15a_amount_law.json). For the untruncated mixture CDF `F`, its density is

`q(x) = f(x) / (F(13000) - F(5000))`, for `5000 <= x <= 13000`, and zero elsewhere.

Sampling procedure for a future implementation:

1. Draw an unrounded proposal from BASE.
2. Accept only if it lies in the fixed USD 5,000..13,000 recipe interval; otherwise repeat the entire mixture proposal.
3. Apply the partition shift described below, if applicable.
4. Check numerical bounds, round once with the shared cent rule, then perform accounting checks.

Every rejection attempt draws a fresh mixture component. Keeping accepted component weights at 90%/10% while separately truncating each component would implement a different distribution. Under conditioning, component weights are proportional to their original weight times their interval probability mass.

There is no uniform USD 5,000..13,000 law. Each S4/H3 motif event receives a fresh conditional proposal; no H3-only amount cloning, precision change or extra jitter is allowed. H3 differs through temporal, repetition and historical structure. If H3 satisfies any complete predicate, its target is 1.

The S4 **target** remains unchanged: its inclusive analytical band is USD 7,000..10,500, or 700,000..1,050,000 cents, together with every other frozen S4 condition. The wider recipe support retains amounts below, inside and above this band. Neither interval represents a legal reporting threshold; the USD 10,000 reference remains a **SYNTHETIC ANALYTICAL THRESHOLD**.

Continuous support conditioning occurs before rounding. All origins use positive-value half-up rounding exactly once at the end: `amount_minor = floor(100*y + 1/2)`. The implementation convention is Decimal from the binary64 value's shortest round-trip decimal representation, multiplied by 100 and quantized with `ROUND_HALF_UP`. Default ties-to-even rounding is not permitted. S4/H3 final amounts must be 500,000..1,300,000 cents inclusive.

## 4. Independent Evaluation: bounded log-space shift

Stage 15 explicitly specifies an Independent amount multiplier of **1.15 = 23/20**, so this clause applies. Ordinary events, including S4/H3 context, retain multiplication by 1.15 and rejection against universal bounds before rounding.

For S4/H3 motifs, first draw `x` from the same `LARGE_CONDITIONAL` law. Apply the following bounded transformation, identically for both origins:

```text
L = 5000; H = 13000
a = ln(L); b = ln(H); w = b-a
delta = ln(23/20)
u = (ln(x)-a)/w
z_prime = ln(x) + 4*delta*u*(1-u)
y = exp(z_prime)
```

At the exact endpoints define `y=L` and `y=H` by continuity. This is the explicit bounded exception to ordinary multiplication: the local amount multiplier is 1 at the endpoints, rises to 1.15 at the geometric midpoint, and stays between those values. It does not multiply every amount by 1.15 and then clip or discard the shifted tail.

The derivative is `1 + (4*delta/w)*(1-2*u)`. Since `4*ln(1.15) < ln(13000/5000)`, it is strictly positive throughout the interval. The transformation is continuous, increasing and fixes both endpoints; therefore its support is exactly USD 5,000..13,000 and it introduces no continuous endpoint mass. Rounding may map a small terminal interval to an endpoint cent, as ordinary cent rounding does; no tail is collapsed there by clipping.

Apply universal and recipe bounds checks, then common rounding, then accounting. An unexpected numerical range error stops implementation for review; it is not repaired by clipping. No target is evaluated during the transformation. No Independent data, salt or stream was created in Stage 15A.

## 5. Q01: episode and motif counts

Let `E` be total episode events. Retain discrete uniform **8..20**, conditioned only on the frozen budget rule. With remaining allocated budget `B>=8`, draw uniformly from `8..min(20,B)`. Residual `B<8` becomes background and is reported, as in Stage 15. All motif and context events count within `E`; there are no added rows.

Given `E`, sample motif count `M` from its declared distribution conditioned on `M<=E`. For a uniform range `[lo,hi]`, the canonical implementation draws directly from `lo..min(hi,E)`. This is the structural conditional law requested; it avoids an unnecessary initial rejected count draw. It neither clips an overlarge `M` nor redraws `E`. Context count is exactly `R=E-M`.

| Family | Motif count before conditioning on E | Status |
| --- | --- | --- |
| S1 | Uniform integers 4..12 | Existing range made explicit |
| S2 | Uniform integers 4..12 | Existing range made explicit |
| S3 | Uniform integers 6..16 | Existing range made explicit |
| S4 | Uniform integers 5..12 | Existing range made explicit |
| N1 | Uniform integers 4..12 | Existing range made explicit |
| N2 | Uniform integers 4..12 | Existing range made explicit |
| N3 | V uniform 2..6; K uniform 0..min(2,E−V); M=V+K | Graph-derived count |
| N4 | Uniform integers 2..20 | Missing count supplied |
| A1 | Uniform integers 8..20 | Missing count supplied |
| A2 | Uniform integers 8..20 | Missing count supplied |
| A3 | Uniform integers 5..16 | Existing range made explicit |
| A4 | Uniform integers 8..20 | Missing count supplied |

N3's primary motif has `V−1` proposed walk edges and one closing proposal. `K=1` adds a parallel prior-edge opportunity; `K=2` adds an alternative two-edge route via an additional active local wallet. Both use the existing monetary and chronological recipe, including its reversed-order opportunities. A proposed closing edge is not a positive label. No path is selected by predicate outcome.

N4 uses one proposed incoming W2W funding event and `M−1` subsequent mixed outward events. Its structural minimum is two; the ceiling reuses 20. A1/A2/A4 reuse the existing 8..20 range, avoiding another arbitrary count scale. Their frozen temporal, customer, concentration and cash rules still apply. These are opportunity counts, not target-support guarantees.

## 6. H1–H8 mapping

Every hard origin uses the same total-episode law and context framework. For a two-family mapping, select one matched recipe with probability 1/2 each before drawing `M`, independently of `E` and evaluated labels. Then use that recipe's exact motif-count law and the relevant frozen hard-origin mechanism.

| Hard origin | Matched count law |
| --- | --- |
| H1 | S1 or S3 |
| H2 | S2 |
| H3 | S4 |
| H4 | N1 |
| H5 | N2 or N4 |
| H6 | N3 |
| H7 | A1 or A3 |
| H8 | A2 or A4 |

H3 uses S4's amount law as well as its count support. H-origin status never assigns a negative label. Full observable predicates determine every event's target, including cross-family positives. Length alone is not assigned a different law to distinguish hard-origin episodes from family opportunities.

## 7. Context-event roles and timing

Each of the `R` context events independently selects one of four roles with probability **1/4**:

| Role | Definition |
| --- | --- |
| Baseline-compatible | Ordinary activity of the episode's focal population using existing parameters; no retroactive baseline insertion or guarantee of target 0 |
| Interleaved unrelated | Ordinary activity of other active subjects in the same local unit, using normal weights |
| Relationship-maintenance | Repeat use of an active partner observed strictly before the current event key; fall back to ordinary active selection if none exists |
| Post-motif ordinary | Ordinary focal-population activity after the motif, with no future recovery used in earlier labels |

All roles use BASE amounts, normal schema, active population/catchment/relationship rules and accounting. If no other active subject exists for unrelated activity, use the ordinary active pool and record the fallback privately. No fallback inspects a target. Every context event is evaluated normally and enters causal history.

Retain the existing family or matched hard-origin **motif** duration `d`. N3 lacks a separate generation duration law; freeze `d~U(1 hour,7 days)` for both N3/H6 proposed graph intervals, solely to define the missing enclosing interval. Its target window remains unchanged.

When `R>0`, draw head and tail fractions `h,t` independently from `U(0.05,0.25)`. Episode duration is `(1+h+t)*d`; draw the episode start uniformly among starts fitting the scored horizon. The motif occupies the original-duration interval after `h*d` of head space. Padding extends the full episode, preserving the motif's temporal constraints. When `R=0`, use the motif interval without padding draws.

Baseline-compatible, unrelated and relationship-maintenance context timestamps are uniform over the full episode interval. Post-motif timestamps are uniform strictly after the motif interval and within the episode tail. This last restriction is the role's meaning; it does not assign a fixed number of last rows, and other context roles may occur after it. There are no compulsory first-two or last-two context positions.

Use integer-microsecond timestamps, random transaction IDs and full-key ordering. Relationship maintenance can use only history already observed at that key; a scheduled future motif does not create prior history. Motif chronology follows its existing recipe, including deliberately reversed graph opportunities where prescribed. No padding event contributes to the ledger before its actual time.

## 8. Private provenance and version normalization

Existing private fields supply the episode identifier (`scenario_id`), origin, intended/matched family (`scenario_family`) and strength. Add only private `event_role` (`motif`/`context`) and `context_role` (one of the four roles, null for motif events). Residual background has no episode role. These fields never enter observables, the binary ground-truth file, the target evaluator, X or prediction inputs.

New files use `amendment_version = v4.stage15a.design.1` and `parent_design_version = v4.stage15.design.1`. Historical `v4.stage 15.design.1` spelling is recorded as an alias of the exact parent hashes; no historical version string is edited.

## 9. Consistency checks and limits

The [test evidence](v4_stage15a_consistency_tests.json) records all 12 requested checks. The [validator](validate_stage15a.py) uses fixed algebraic values, exact discrete probability arithmetic and file hashes. It instantiates no random generator, creates no events or labels, and imports no evaluator or feature extractor.

| Test | Static/design check | Result |
| --- | --- | --- |
| T01 | One conditional S4 mixture implementation, correct conditioning and common rounding | PASS |
| T02 | H3 and S4 reference exactly the same conditional law and shift | PASS |
| T03 | Frozen S4 target band remains 700,000..1,050,000 cents | PASS |
| T04 | Recipe support remains 500,000..1,300,000 cents, including bounded shift | PASS |
| T05 | Rejection is numerical/structural only; no target-dependent sampling | PASS |
| T06 | All 12 family mappings valid for every E=8..20 | PASS |
| T07 | All eight hard-origin mappings valid for every E=8..20 | PASS |
| T08 | Context enters the universal evaluator/history without forced labels | PASS |
| T09 | Target predicates unchanged and outside override scope | PASS |
| T10 | A1 35d/12-service contract and gates unchanged | PASS |
| T11 | 100,000+24,000, partition sizes and isolated entities unchanged | PASS |
| T12 | 746 protected historical/Stage 15/failed Stage 16 files unchanged | PASS |

The count audit exhausts all family and hard-origin supports and verifies probability mass exactly. The shift audit checks its monotonicity bound, endpoints and interior support algebraically, with a deterministic numerical grid as an additional arithmetic check. These are not empirical distribution, runtime, generator-causality or dataset-quality tests. No increased family support or reduced shortcut discrimination is claimed.

Preservation covers 702 inherited historical/application files, 21 original Stage 15 files and 23 failed Stage 16 report/evidence/source files. Before/after SHA-256 values match; changed paths are empty. No V3 evaluation tree or V4 evaluation data was inspected or created. Named V3 public commitments are metadata-only checks; unread evaluation bytes remain outside the claim.

No direct contradiction with model candidates, the 36-fit ceiling, threshold policy, metrics or holdout governance was found in this amendment's scope. The Independent S4/H3 shift exception is explicitly listed in precedence C. A future implementation must still pass its own schema, causality, accounting, isolation, target-replay, runtime and population gates.

## 10. Deliverables and decision

- [Amount law](v4_stage15a_amount_law.json)
- [Episode mapping](v4_stage15a_episode_mapping.json)
- [Precedence](v4_stage15a_precedence.json)
- [Consistency tests](v4_stage15a_consistency_tests.json)
- [Manifest and preservation](v4_stage15a_manifest.json)
- [Decision](v4_stage15a_decision.json)

For a read-only recheck: `python -B ml_v4/design/amendments/validate_stage15a.py`. The validator checks saved artifact hashes and protected inputs. It does not retry Stage 16.

**A — STAGE 15A AMENDMENT APPROVED; STAGE 16 MAY BE RETRIED.**

All 12 consistency tests pass. Stage 15A ends here; Stage 16 remains unexecuted after this amendment and requires a separately authorized retry in a fresh attempt namespace. No data, labels, features, holdout seals, model fits or threshold searches were created.

**V4 STAGE 15A COMPLETE — WAITING FOR APPROVAL.**
