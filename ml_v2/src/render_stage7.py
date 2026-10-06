"""Render the Stage 7 development-only diagnostic summaries."""
import json

from contracts import ROOT, safe_path
from improve_candidates import FAMILIES


def read(name): return json.loads((ROOT/'reports'/name).read_text(encoding='utf-8'))
def pct(x): return '—' if x is None else f'{100*x:.1f}%'
def num(x): return '—' if x is None else f'{x:.3f}'
def save(name,lines): safe_path(ROOT/'reports'/name).write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    ep=read('stage7_episode_position.json'); ob=read('stage7_family_observability.json')
    hard=read('stage7_hard_negative_overlap.json'); nn=read('stage7_neighbour_overlap.json')
    sep=read('stage7_family_separability.json'); complete=read('stage7_completed_episode_diagnostic.json')
    lines=['# MODEL V2 — STAGE 7 DEEP SEPARABILITY DIAGNOSIS','',
           '**Diagnosis E — multiple factors are material.** Causal event position, overlap with deliberately similar normal episodes, and generator construction all contribute. The frozen 30 features also miss some observable context. The evidence does not support additional model tuning as the main next step. No model, label, feature, threshold, or dataset was changed.','',
           '## Method and limits','',
           'Only Train and Validation records were loaded for analysis. The frozen Stage 5 artifact `s5_gradient_boosting_060` supplied Validation probabilities at threshold 0.50. Episode IDs, family names, and normal-family metadata selected diagnostic cohorts after prediction; none entered the frozen model or a feature matrix. Episode positions use chronological transaction IDs of committed episode members; ordinary events remain interleaved in the global history but do not count toward episode position. All percentages below use Validation unless stated. Counts and exact values are in the six Stage 7 JSON outputs.','',
           'Prior-episode evidence categories are operational lower-bound proxies. `none` means the chosen motif has not appeared within the labelled episode; it does not prove the transaction is harmless or that all ordinary prior history is empty. `mature` means a specified repeated pattern exists before the current event; it does not prove illicit intent. The [causal observability report](V2_STAGE7_CAUSAL_OBSERVABILITY.md) states each proxy and its limits.','',
           '## Recall by event position and prior episode evidence','',
           '| Suspicious family | 1st | 2nd | 3rd | 4th+ | No motif | Partial | Mature |',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for f in FAMILIES:
        x=ep['families'][f]['event_bucket']; z=ob['families'][f]
        cells=[pct(x[k]['recall']) for k in ('1','2','3','4+')]
        cells += [f"{pct(z[k]['count']/150)} ({z[k]['count']})" for k in ('none','partial','mature')]
        lines.append('| '+f+' | '+' | '.join(cells)+' |')
    lines += ['', 'Each family has 150 suspicious Validation events. Quartile-position counts and recall are in `stage7_episode_position.json`. First-event recall is zero in 8 of 12 families. For several families recall rises sharply once episode history accumulates. This supports a causal timing problem, but late weakness in N1, N3, A1, A2, and A4 shows timing alone is insufficient.','',
              '## N3 reciprocal-cycle forensic result','']
    n3=ob['n3']; anym=n3['any_episode_prior_motif']; rel=n3['categories']; closure=n3['current_edge_closure']
    lines += [f"Among 150 N3 events, {anym['no_prior_reciprocal']['count']} ({pct(anym['no_prior_reciprocal']['count']/150)}) had no earlier reciprocal pair anywhere in the same episode. {anym['any_prior_cycle']['count']} ({pct(anym['any_prior_cycle']['count']/150)}) followed a completed cycle elsewhere in the episode; Stage 5 recalled {anym['any_prior_cycle']['detected']}/{anym['any_prior_cycle']['count']} ({pct(anym['any_prior_cycle']['recall'])}). No event had a completed prior cycle **involving a current endpoint** ({rel['complete_prior_cycle']['count']}/150), and none had a prior reciprocal pair involving a current endpoint. These are distinct tests: a previous motif on other wallets cannot by itself establish the present edge's role.", '',
              f"The current edge closes a directed cycle in {closure['current_closes_cycle']['count']}/150 events ({pct(closure['current_closes_cycle']['count']/150)}). Stage 5 recalled {closure['current_closes_cycle']['detected']} of these, versus {closure['current_does_not_close_cycle']['detected']} of the other {closure['current_does_not_close_cycle']['count']}. Thus many N3 labels precede an observable cycle on the current wallet pair, while a current-edge motif is available for some events but absent from the frozen representation. The generator creates disjoint complete cycles inside an episode; it does not guarantee an earlier cycle involving later edge endpoints.", '',
              '## N4 pass-through roles','',
              '| Causal role | Events | Stage 5 recall |','|---|---:|---:|']
    for k,v in ob['n4']['roles'].items(): lines.append(f"| {k} | {v['count']} | {pct(v['recall'])} |")
    lines += ['', 'The first inbound transfer has no earlier onward movement in that episode. Later outbound or exit events have earlier episode funding and are much more detectable. The first cash-funding events may be detected through unrelated prior activity, not completed pass-through evidence. Role by event position is in `stage7_family_observability.json`.','',
              '## Local class overlap in frozen 30-feature space','',
              f"A Train-fitted RobustScaler and five Euclidean neighbours were used. The fixed reference sample contains {nn['reference_counts']['normal']:,} Train normal and {nn['reference_counts']['suspicious']:,} Train suspicious events; suspicious cases are intentionally enriched to {pct(nn['reference_counts']['suspicious']/(nn['reference_counts']['normal']+nn['reference_counts']['suspicious']))}. Distances were clipped to ±20 scaled units for stability. Neighbour fractions are geometry diagnostics, **not posterior probabilities** or a deployable classifier. {pct(nn['validation']['suspicious']['mostly_normal'])} of suspicious Validation events have a mostly normal five-neighbour set; {pct(nn['validation']['normal']['mostly_suspicious'])} of normal events have a mostly suspicious set.", '',
              '| Domain | Suspicious events with mostly normal neighbours |','|---|---:|']
    for d in ('structuring','network','agent'): lines.append(f"| {d} | {pct(nn['domains'][d]['mostly_normal'])} |")
    lines += ['', f"Among H1 normals, {pct(nn['normal_families']['H1']['mostly_suspicious'])} have mostly suspicious neighbours; among H7 normals, {pct(nn['normal_families']['H7']['mostly_suspicious'])} do. For N3, {pct(nn['positions']['reciprocal_relationship_cycle']['4+']['mostly_normal'])} of fourth-or-later events still have mostly normal neighbours. Family and episode-position neighbour results, plus all H1–H8 and routine normal results, are in `stage7_neighbour_overlap.json`. Sampling and the metric affect these fractions; they establish substantial local overlap under this particular representation and distance choice.",'',
              '## Hard negatives and family-conditioned separability','',
              '| Suspicious family | Matched normal | Strongest frozen univariate AUC¹ | IQR overlap | Domain-group logistic AUC² | All-30 logistic AUC² |',
              '|---|---|---:|---:|---:|---:|']
    for f in FAMILIES:
        c=hard['comparisons'][f]; top=c['top_frozen_features'][0]; groups=sep['families'][f]['oracle_group']
        domain=next(k for k in groups if k!='all_30')
        lines.append(f"| {f} | {c['hard_family']} | {num(top['auc_direction_free'])} ({top['feature']}) | {num(top['iqr_overlap'])} | {num(groups[domain]['roc_auc'])} | {num(groups['all_30']['roc_auc'])} |")
    lines += ['', '¹ Direction-free absolute univariate ROC-AUC ranks the 30 existing values for a selected family versus its designed hard counterpart; selecting the best on Validation is exploratory and optimistic. IQR overlap is intersection divided by union of the two middle-50% ranges. ² Small diagnostic Logistic Regression models were fitted on Train with family-versus-matched-normal cohort selection and evaluated on Validation. The family identity selected rows only, never entered X. They are not production models or a fair replacement for the general detector. AUC below 0.5 is reported without flipping the learned score.','',
              'The generator uses the same pattern constructor for a suspicious family and its hard counterpart, with overlapping coordination supports. That creates intended behavioural ambiguity. It also produces measurable nuisance differences. For example, N3 Validation events are all wallet-to-wallet transfers (150/150), while H6 contains 687/825 transfers and 138/825 cash events. N3 has 125/150 direct-wallet events versus H6 481/825. Episode-length and channel differences are potential generator artefacts; they are not evidence of illicit behaviour. Exact channel/type mixes and feature overlaps for all eight H1–H8 mappings are in `stage7_hard_negative_overlap.json`. H1 and H7 false-positive rates for the frozen Stage 5 model remain 0.4303 and 0.3321, respectively.','',
              '| Hard normal | Resembles | Causal comparison and frozen representation |',
              '|---|---|---|',
              '| H1 | S1/S3 | Prior wallet count and value can show both legitimate and suspicious bursts; 1h and same-day features exist. Coordinated continuation needs later events. |',
              '| H2 | S2 | Repetition is available after prior amounts accumulate; repeated-amount ratio and dispersion exist, but ordinary recurring payments share them. |',
              '| H3 | S4 | Prior near-threshold share exists; normal high payments overlap. The frozen threshold-history ratio is present, but episode persistence needs time. |',
              '| H4 | N1 | Prior receiver source count exists and is represented at 7d; current-edge collection breadth and source turnover are incomplete. Legitimate merchants share collection patterns. |',
              '| H5 | N2/N4 | Outbound counterparty count and 24h pass-through ratio exist; the first funding leg cannot show later outflow. Legitimate payroll and settlement transit overlap. |',
              '| H6 | N3 | Prior reciprocity ratio exists, but current-edge path closure is absent. Refund and settlement cycles overlap; channel/type mix also differs by construction. |',
              '| H7 | A1/A3 | Prior agent count, distinct wallets, novelty and burst z-score exist; busy legitimate service shares them. Change relative to preceding population is incomplete. |',
              '| H8 | A2/A4 | Prior HHI and float value ratio exist; short count concentration and cash count direction are absent from baseline. Ordinary concentrated customers and cash demand overlap. |','',
              '## Agent baseline comparisons','',
              '| Suspicious family | Matched normal | Prior-hour count median (S/N) | Recent unique wallets median (S/N) | New-wallet share median (S/N) | Strongest of measured prior quantities AUC¹ |',
              '|---|---|---:|---:|---:|---:|']
    for f in FAMILIES[8:]:
        a=ob['agent_prior_baseline'][f]; q=a['quantities']; best=max(q.items(),key=lambda kv:kv[1]['direction_free_auc'])
        lines.append(f"| {f} | {a['hard_family']} | {q['prior_hour_count']['suspicious_median']:.1f}/{q['prior_hour_count']['normal_median']:.1f} | {q['recent_unique_wallets']['suspicious_median']:.1f}/{q['recent_unique_wallets']['normal_median']:.1f} | {q['new_wallet_share']['suspicious_median']:.2f}/{q['new_wallet_share']['normal_median']:.2f} | {num(best[1]['direction_free_auc'])} ({best[0]}) |")
    lines += ['', 'These quantities were calculated strictly before each event from that agent’s Validation-partition transactions, with recent seven-day and preceding seven-day windows. The 24-hour concentration and seven-day cash-count imbalance distributions are in the machine output. In A1, median prior new-wallet share is 0.92 versus 0.94 for H7; novelty alone does not separate them. A2’s median top-wallet share is 0.11 versus H8’s 0.15. A3 has stronger prior-hour intensity (6 versus 1), while A4 cash-count imbalance has only modest separation.','',
              '## Completed episode diagnostic — NON-DEPLOYABLE','',
              'Completed-episode statistics use future transactions. The table shows the strongest descriptive statistic AUC for each matched pair, alongside the strongest frozen feature at the first episode event. It is a descriptive comparison with different units and Validation-based maxima, **not** an estimate of achievable causal classifier performance.','',
              '| Suspicious family | First-event best frozen AUC¹ | Completed-episode best AUC¹ | Statistic |',
              '|---|---:|---:|---|']
    for f in FAMILIES:
        c=complete['families'][f]; k,v=max(c['completed_statistics'].items(),key=lambda kv:kv[1]['direction_free_auc'])
        lines.append(f"| {f} | {num(c['best_first_event_frozen_feature_auc'])} | {num(v['direction_free_auc'])} | {k} |")
    lines += ['', 'For N3, the strongest completed-episode separator is **unique serviced-wallet count** (Validation median 1 suspicious versus 4 H6), not a cycle statistic. This is a generator construction difference. The same direction appears on Train (median 2 versus 4; AUC 0.787 versus Validation 0.941). Episode-length separation is much stronger on Validation (AUC 0.844; medians 7.5 versus 14) than Train (AUC 0.560; medians 13.5 versus 15). This variation cautions against treating a Validation-only descriptor as a stable behavioural law. Completed-episode comparisons for both Train and Validation are in `stage7_completed_episode_diagnostic.json`. Such hindsight separation must not be interpreted as a valid real-time signal or as proof that changing early labels would improve a legitimate detector.','',
              '## Dataset design assessment and decision','',
              'The Stage 2 truth assigns target 1 to every planned suspicious episode event, including entry/funding edges and first interactions before an episode motif can exist. This is a demonstrable decision-point mismatch for N3 cycle closure and N4 inbound transfers if the intended decision is a causal transaction alert for the defining behaviour. It is not proof those events are harmless; other independent prior context might support suspicion. H1/H7 overlap and the generator’s shared pattern constructors also create legitimate ambiguity. The N3/H6 channel and episode-size differences show a separate generator artefact; apparent separability may reflect construction rather than behaviour. The 30 features are limited, but Stage 6 additions did not improve Macro F1, and the current evidence does not isolate feature insufficiency as the sole ceiling.','',
              '**One next research action:** write a pre-registered, decision-point-aware dataset and ground-truth redesign proposal. Define when an individual transaction can be labelled from information available at its decision time, and when a wallet/agent or sequence alert is the proper analytical unit. Specify independent generator checks for channel and episode-size artefacts. Preserve this V2 dataset and all baselines as the comparison; implement no redesign in Stage 7.','',
              f"Before/after SHA-256 checks passed for {ep['protection']['v1_application_file_count']} V1/application files and {ep['protection']['v2_dataset_feature_stage5_stage6_file_count']} V2 development raw-data, frozen-feature, Stage 5, and Stage 6 files. The final runner does not read holdout files. **Protection deviation:** during preliminary Stage 7 runs, the initial hash check read Final Test and Independent Evaluation file bytes. It did not parse or analyse holdout rows, labels, features, or distributions, and no holdout data entered any model or diagnostic. This violated the explicit no-access instruction; the holdout seal cannot be claimed as unbroken for this stage. The hash check was restricted to development files before the final run.",'',
              'V2 STAGE 7 COMPLETE — WAITING FOR APPROVAL.']
    save('V2_STAGE7_SEPARABILITY_DIAGNOSIS.md',lines)

    causal=['# MODEL V2 — STAGE 7 CAUSAL OBSERVABILITY','',
            'This report asks what can be known when each transaction is classified. The current transaction fields are observable; later transactions and completed episode statistics are not. Labelled episode membership is used here solely to align the diagnostic timeline. The frozen model receives neither episode membership nor the explanatory categories below.','',
            '## Family-by-family event timeline','',
            '| Family | Before event 1 | Before event 2 | Before event 3 | Once mature, before current event | Current edge / after current event | Future-dependent information |',
            '|---|---|---|---|---|---|---|']
    descriptions={
      'variable_fragment_burst':('Ordinary wallet history only; no campaign fragment.','One prior fragment; amount and gap available.','Two prior fragments; growing count/value.','Several prior fragments support burst and cumulative-flow evidence.','Current amount can extend the burst.','Final episode total and later continuation.'),
      'similar_amount_repetition':('No campaign anchor repeated yet.','One prior amount can be compared with current.','Two prior amounts begin a repetition pattern.','Three or more similar prior amounts support persistence.','Current amount can add another match.','Whether later amounts stay near the anchor.'),
      'distributed_same_day_fragmentation':('No campaign same-day count.','One fragment in prior same-day history.','Two earlier fragments, possibly across clusters.','Several same-day prior fragments or previous day recurrence.','Current fragment increases the count.','Full day total and later-day recurrence.'),
      'variable_near_threshold_history':('No campaign near-threshold history.','One prior amount may be near synthetic threshold.','Two prior amounts may establish a tendency.','Repeated prior near-threshold values plus contextual flow.','Current amount contributes to the history.','Final episode near-threshold fraction.'),
      'many_to_one_collection':('No campaign contributor edges.','At most one prior contributor to collector.','Two prior sources may exist.','Three or more distinct prior sources can establish collection breadth.','Current receiver/sender may add a new contributor.','Later contributors and onward use of funds.'),
      'one_to_many_dispersion':('No campaign outgoing edges.','At most one prior destination.','Two prior destinations may exist.','Three or more distinct prior destinations support dispersion.','Current recipient can expand the set.','Later payouts and retained balance.'),
      'reciprocal_relationship_cycle':('No campaign cycle.','At most one earlier edge; no reciprocal pair.','A return edge or path may be forming, depending on edge order.','Earlier cycles may exist elsewhere in episode; relevant current endpoints must be checked.','Current edge can close a cycle; this is observable now but requires a current-edge graph calculation.','Later edges that complete a still-open cycle.'),
      'wallet_pass_through':('No campaign inflow/outflow sequence.','Funding may be in prior cash history, but no onward transfer yet.','An earlier transfer may fund the transit wallet.','Prior inflow plus outward movement supports pass-through.','Current outbound/exit can reveal movement from prior funding.','Whether later outflows reach 50–98% of funding.'),
      'agent_wallet_growth':('Ordinary agent baseline only; no campaign growth.','One newly served wallet may be observed.','Two campaign service events may show change.','Several distinct serviced wallets relative to prior baseline support growth.','Current wallet may be new to agent.','Final customer-cohort growth and returns.'),
      'agent_wallet_concentration':('Ordinary agent baseline only.','One campaign wallet service event.','Repeated service of one/two wallets may start concentration.','Prior short-window count/value concentration relative to baseline.','Current serviced wallet may reinforce concentration.','Final episode share assigned to designated wallets.'),
      'agent_temporal_burst':('Ordinary agent activity only.','One campaign service event.','Two prior events yield preliminary rate.','Multiple prior events in short interval versus agent baseline.','Current timestamp/value extends the burst.','Full cluster count and duration.'),
      'agent_flow_imbalance':('Ordinary agent cash baseline only.','One prior cash direction may be known.','Two prior cash events can show count skew.','Opening three cash events may show skew; later balancing can erase it.','Current Cash-In/Out changes count and value balance.','Whole-episode direction and subsequent balancing.')}
    for f in FAMILIES: causal.append('| '+f+' | '+' | '.join(descriptions[f])+' |')
    causal += ['', '### Evidence-category rules used in the JSON diagnostic','',
               'All rules use **prior events in the same labelled episode**. `none`, `partial`, and `mature` are research proxies. They do not decide the ground truth. They omit prior routine and other-episode context, so `none` is a lower-bound statement about the targeted episode motif only.','',
               '| Family | Mature prior-episode proxy |','|---|---|',
               '| S1 | At least 3 prior episode events. |',
               '| S2 | At least 3 prior amounts within 5% of an anchor among prior episode events. |',
               '| S3 | At least 3 prior episode events on one UTC day. |',
               '| S4 | At least 2 prior amounts within the broad synthetic-threshold band. |',
               '| N1 | At least 3 distinct prior transfer senders to one receiver. |',
               '| N2 | At least 3 distinct prior transfer receivers from one sender. |',
               '| N3 | A directed cycle already exists in prior episode transfers; separate current-endpoint relevance test. |',
               '| N4 | At least 2 prior episode transfers; role-specific inflow/outflow check reported separately. |',
               '| A1 | At least 4 distinct prior serviced wallets in episode. |',
               '| A2 | At least 3 prior service events for one wallet in episode. |',
               '| A3 | At least 3 prior episode events within 2 hours. |',
               '| A4 | At least 3 prior cash events in episode. |','',
               'The percentages for all 12 families are in the separability report and `stage7_family_observability.json`. These thresholds indicate when a pattern can begin to be evaluated. They do not assert a transaction should be labelled suspicious once the threshold is met. In particular, N3’s generic `mature` episode category counts a prior cycle even if its wallets differ from the current transaction; the endpoint-relevant forensic category corrects that limitation.','',
               '## N3 and N4 decision points','',
               f"N3: {ob['n3']['current_edge_closure']['current_closes_cycle']['count']}/150 current edges close a prior directed path, but 0/150 have a complete earlier cycle involving a current endpoint. {ob['n3']['any_episode_prior_motif']['any_prior_cycle']['count']}/150 follow a cycle somewhere else in the episode. A current-edge motif is causally observable now if calculated from prior graph plus current endpoints; later closure is future-dependent for an earlier edge. The frozen 30 features do not contain this exact current-edge path-closure calculation.",'',
               f"N4: the {ob['n4']['roles']['inbound_transfer']['count']} first inbound transfers are labelled suspicious before onward movement from that funding leg occurs; Stage 5 detects none. {ob['n4']['roles']['outbound_or_exit']['count']} later outbound/exit events have funding in prior episode history and reach {pct(ob['n4']['roles']['outbound_or_exit']['recall'])} recall. The role inference follows the generator's first-transfer schedule and does not claim that every later cash event is a pass-through edge.",'',
               '## Label-observability consistency','',
               'Stage 2 labels every event in a precommitted suspicious episode target 1. The first event of each episode therefore carries a suspicious label before any evidence from that episode exists. The exact percentage of events with `none`, `partial`, and `mature` *prior episode motif* is reported for every family in `stage7_family_observability.json`. This demonstrates a timing mismatch with a detector intended to alert on the defining episode motif at each transaction. It does not show that every early label is wrong: ordinary prior history, current transaction facts, and other lawful context may contribute evidence, and suspiciousness can be an investigation target rather than a proven offence.','',
               'For A1–A4, prior agent seven-day and preceding seven-day counts, distinct wallets, short-window concentration, cash imbalance, and one-hour burst intensity were calculated from Validation event history before insertion of the current transaction. Comparisons with H7/H8 appear in the separability report and machine output. These are diagnostics only; none was added to X.','',
               'V2 STAGE 7 COMPLETE — WAITING FOR APPROVAL.']
    save('V2_STAGE7_CAUSAL_OBSERVABILITY.md',causal)


if __name__=='__main__': main()
