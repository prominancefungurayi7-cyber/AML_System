# MODEL V2 — STAGE 7 CAUSAL OBSERVABILITY

This report asks what can be known when each transaction is classified. The current transaction fields are observable; later transactions and completed episode statistics are not. Labelled episode membership is used here solely to align the diagnostic timeline. The frozen model receives neither episode membership nor the explanatory categories below.

## Family-by-family event timeline

| Family | Before event 1 | Before event 2 | Before event 3 | Once mature, before current event | Current edge / after current event | Future-dependent information |
|---|---|---|---|---|---|---|
| variable_fragment_burst | Ordinary wallet history only; no campaign fragment. | One prior fragment; amount and gap available. | Two prior fragments; growing count/value. | Several prior fragments support burst and cumulative-flow evidence. | Current amount can extend the burst. | Final episode total and later continuation. |
| similar_amount_repetition | No campaign anchor repeated yet. | One prior amount can be compared with current. | Two prior amounts begin a repetition pattern. | Three or more similar prior amounts support persistence. | Current amount can add another match. | Whether later amounts stay near the anchor. |
| distributed_same_day_fragmentation | No campaign same-day count. | One fragment in prior same-day history. | Two earlier fragments, possibly across clusters. | Several same-day prior fragments or previous day recurrence. | Current fragment increases the count. | Full day total and later-day recurrence. |
| variable_near_threshold_history | No campaign near-threshold history. | One prior amount may be near synthetic threshold. | Two prior amounts may establish a tendency. | Repeated prior near-threshold values plus contextual flow. | Current amount contributes to the history. | Final episode near-threshold fraction. |
| many_to_one_collection | No campaign contributor edges. | At most one prior contributor to collector. | Two prior sources may exist. | Three or more distinct prior sources can establish collection breadth. | Current receiver/sender may add a new contributor. | Later contributors and onward use of funds. |
| one_to_many_dispersion | No campaign outgoing edges. | At most one prior destination. | Two prior destinations may exist. | Three or more distinct prior destinations support dispersion. | Current recipient can expand the set. | Later payouts and retained balance. |
| reciprocal_relationship_cycle | No campaign cycle. | At most one earlier edge; no reciprocal pair. | A return edge or path may be forming, depending on edge order. | Earlier cycles may exist elsewhere in episode; relevant current endpoints must be checked. | Current edge can close a cycle; this is observable now but requires a current-edge graph calculation. | Later edges that complete a still-open cycle. |
| wallet_pass_through | No campaign inflow/outflow sequence. | Funding may be in prior cash history, but no onward transfer yet. | An earlier transfer may fund the transit wallet. | Prior inflow plus outward movement supports pass-through. | Current outbound/exit can reveal movement from prior funding. | Whether later outflows reach 50–98% of funding. |
| agent_wallet_growth | Ordinary agent baseline only; no campaign growth. | One newly served wallet may be observed. | Two campaign service events may show change. | Several distinct serviced wallets relative to prior baseline support growth. | Current wallet may be new to agent. | Final customer-cohort growth and returns. |
| agent_wallet_concentration | Ordinary agent baseline only. | One campaign wallet service event. | Repeated service of one/two wallets may start concentration. | Prior short-window count/value concentration relative to baseline. | Current serviced wallet may reinforce concentration. | Final episode share assigned to designated wallets. |
| agent_temporal_burst | Ordinary agent activity only. | One campaign service event. | Two prior events yield preliminary rate. | Multiple prior events in short interval versus agent baseline. | Current timestamp/value extends the burst. | Full cluster count and duration. |
| agent_flow_imbalance | Ordinary agent cash baseline only. | One prior cash direction may be known. | Two prior cash events can show count skew. | Opening three cash events may show skew; later balancing can erase it. | Current Cash-In/Out changes count and value balance. | Whole-episode direction and subsequent balancing. |

### Evidence-category rules used in the JSON diagnostic

All rules use **prior events in the same labelled episode**. `none`, `partial`, and `mature` are research proxies. They do not decide the ground truth. They omit prior routine and other-episode context, so `none` is a lower-bound statement about the targeted episode motif only.

| Family | Mature prior-episode proxy |
|---|---|
| S1 | At least 3 prior episode events. |
| S2 | At least 3 prior amounts within 5% of an anchor among prior episode events. |
| S3 | At least 3 prior episode events on one UTC day. |
| S4 | At least 2 prior amounts within the broad synthetic-threshold band. |
| N1 | At least 3 distinct prior transfer senders to one receiver. |
| N2 | At least 3 distinct prior transfer receivers from one sender. |
| N3 | A directed cycle already exists in prior episode transfers; separate current-endpoint relevance test. |
| N4 | At least 2 prior episode transfers; role-specific inflow/outflow check reported separately. |
| A1 | At least 4 distinct prior serviced wallets in episode. |
| A2 | At least 3 prior service events for one wallet in episode. |
| A3 | At least 3 prior episode events within 2 hours. |
| A4 | At least 3 prior cash events in episode. |

The percentages for all 12 families are in the separability report and `stage7_family_observability.json`. These thresholds indicate when a pattern can begin to be evaluated. They do not assert a transaction should be labelled suspicious once the threshold is met. In particular, N3’s generic `mature` episode category counts a prior cycle even if its wallets differ from the current transaction; the endpoint-relevant forensic category corrects that limitation.

## N3 and N4 decision points

N3: 48/150 current edges close a prior directed path, but 0/150 have a complete earlier cycle involving a current endpoint. 80/150 follow a cycle somewhere else in the episode. A current-edge motif is causally observable now if calculated from prior graph plus current endpoints; later closure is future-dependent for an earlier edge. The frozen 30 features do not contain this exact current-edge path-closure calculation.

N4: the 14 first inbound transfers are labelled suspicious before onward movement from that funding leg occurs; Stage 5 detects none. 111 later outbound/exit events have funding in prior episode history and reach 60.4% recall. The role inference follows the generator's first-transfer schedule and does not claim that every later cash event is a pass-through edge.

## Label-observability consistency

Stage 2 labels every event in a precommitted suspicious episode target 1. The first event of each episode therefore carries a suspicious label before any evidence from that episode exists. The exact percentage of events with `none`, `partial`, and `mature` *prior episode motif* is reported for every family in `stage7_family_observability.json`. This demonstrates a timing mismatch with a detector intended to alert on the defining episode motif at each transaction. It does not show that every early label is wrong: ordinary prior history, current transaction facts, and other lawful context may contribute evidence, and suspiciousness can be an investigation target rather than a proven offence.

For A1–A4, prior agent seven-day and preceding seven-day counts, distinct wallets, short-window concentration, cash imbalance, and one-hour burst intensity were calculated from Validation event history before insertion of the current transaction. Comparisons with H7/H8 appear in the separability report and machine output. These are diagnostics only; none was added to X.

V2 STAGE 7 COMPLETE — WAITING FOR APPROVAL.
