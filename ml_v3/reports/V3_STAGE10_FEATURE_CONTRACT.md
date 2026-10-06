# MODEL V3 ? STAGE 10 FEATURE CONTRACT

**Status: FROZEN BEFORE MATRIX EXTRACTION**

The representation contains exactly 32 ordered numeric features. Missing or ineligible ratios use the finite sentinel `-1.0`; legitimate zero remains `0.0`. Every history lookup is partition-local and uses `(event_timestamp, transaction_id) < current key`. State is updated only after the current vector is emitted.

## Ordered feature list

1. `current_amount_usd` ? **current** ? current transaction amount / 100 USD ? `current`
2. `current_is_cash_in` ? **current** ? 1 iff current transaction_type is cash_in ? `current`
3. `current_is_cash_out` ? **current** ? 1 iff current transaction_type is cash_out ? `current`
4. `wallet_count_1h_inclusive` ? **structuring** ? count of subject-wallet events in [T-1h,T] ? `prior+current`
5. `wallet_value_24h_inclusive` ? **structuring** ? sum of subject-wallet amounts in [T-24h,T] ? `prior+current`
6. `wallet_count_utc_day_inclusive` ? **structuring** ? count of subject-wallet events since UTC midnight through T ? `prior+current`
7. `wallet_active_hours_utc_day` ? **structuring** ? distinct UTC hour buckets for subject-wallet events since midnight through T ? `prior+current`
8. `wallet_current_amount_cluster_share_7d` ? **structuring** ? share of subject-wallet events in [T-7d,T] within 5% of current amount ? `prior+current`
9. `wallet_band_share_7d_inclusive` ? **structuring** ? share of subject-wallet events in [T-7d,T] in 7000..10500 USD ? `prior+current`
10. `wallet_count_acceleration_1h` ? **structuring** ? inclusive 1h count / max(1, prior-28d count / 672) ? `prior+current`
11. `receiver_unique_sources_24h_inclusive` ? **network** ? distinct W2W senders to receiver in [T-24h,T] ? `prior+current`
12. `receiver_inflow_count_24h_inclusive` ? **network** ? W2W inflow count to receiver in [T-24h,T] ? `prior+current`
13. `receiver_inflow_acceleration_24h` ? **network** ? inclusive receiver inflow count / max(1, prior-28d inflow count / 28) ? `prior+current`
14. `sender_unique_destinations_24h_inclusive` ? **network** ? distinct W2W receivers from sender in [T-24h,T] ? `prior+current`
15. `sender_outflow_count_24h_inclusive` ? **network** ? W2W outflow count from sender in [T-24h,T] ? `prior+current`
16. `sender_outflow_acceleration_24h` ? **network** ? inclusive sender outflow count / max(1, prior-28d count / 28) ? `prior+current`
17. `current_return_path_length` ? **network** ? shortest simple prior path receiver to sender, 1..5 edges in 7d; zero otherwise ? `prior-only plus current endpoints`
18. `current_return_amount_ratio` ? **network** ? current amount / first-edge amount of selected prior return path; -1 when absent ? `prior-only plus current amount`
19. `wallet_observed_onward_funding_share_24h` ? **network** ? observed outward value after prior funding anchor / observed funding value ? `prior+current for outflow`
20. `wallet_prior_funding_age_hours` ? **network** ? hours from prior funding anchor to current outflow; -1 when absent ? `prior-only plus current timestamp`
21. `agent_service_count_1h_inclusive` ? **agent** ? agent service-event count in [T-1h,T]; zero for direct W2W ? `prior+current`
22. `agent_service_acceleration_1h` ? **agent** ? inclusive service count / max(1, preceding-28d service count / 672); -1 if coverage insufficient ? `prior+current`
23. `agent_wallet_growth_ratio_7d` ? **agent** ? recent inclusive distinct serviced wallets / max(1, median of four preceding 7d counts); -1 if insufficient ? `prior+current`
24. `agent_new_wallet_share_7d` ? **agent** ? recent serviced-wallet fraction absent from preceding-28d wallet union; -1 if insufficient ? `prior+current`
25. `agent_top2_count_share_24h` ? **agent** ? top-two serviced-wallet service-event share in [T-24h,T] ? `prior+current`
26. `agent_top2_share_change_24h` ? **agent** ? inclusive top-two share minus preceding-28d top-two share; -1 if insufficient ? `prior+current`
27. `agent_cash_value_skew_24h` ? **agent** ? (CashOut value-CashIn value)/(sum) in [T-24h,T] ? `prior+current`
28. `agent_cash_count_skew_24h` ? **agent** ? corresponding signed event-count skew in [T-24h,T] ? `prior+current`
29. `agent_cash_value_skew_change` ? **agent** ? inclusive cash value skew minus preceding-28d cash value skew; -1 if insufficient ? `prior+current`
30. `wallet_history_coverage_days` ? **coverage** ? partition-local subject-wallet observation span before T, capped at 28 days ? `prior-only`
31. `receiver_history_coverage_days` ? **coverage** ? partition-local receiver observation span before T, capped at 28 days ? `prior-only`
32. `agent_history_coverage_days` ? **coverage** ? partition-local agent observation span before T, capped at 28 days; zero without agent ? `prior-only`

## Per-feature contract

### 1. `current_amount_usd`

- **Behavioural domain / subject:** The subject is the current transaction or its observable principal endpoint. Current amount/type facts are used; no prior state is required. Cash-In sets only the Cash-In indicator, Cash-Out sets only the Cash-Out indicator, and W2W sets both to zero. Cold start is a valid amount/type value; no denominator applies.
- **Mathematical definition:** current transaction amount / 100 USD.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 2. `current_is_cash_in`

- **Behavioural domain / subject:** The subject is the current transaction or its observable principal endpoint. Current amount/type facts are used; no prior state is required. Cash-In sets only the Cash-In indicator, Cash-Out sets only the Cash-Out indicator, and W2W sets both to zero. Cold start is a valid amount/type value; no denominator applies.
- **Mathematical definition:** 1 iff current transaction_type is cash_in.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 3. `current_is_cash_out`

- **Behavioural domain / subject:** The subject is the current transaction or its observable principal endpoint. Current amount/type facts are used; no prior state is required. Cash-In sets only the Cash-In indicator, Cash-Out sets only the Cash-Out indicator, and W2W sets both to zero. Cold start is a valid amount/type value; no denominator applies.
- **Mathematical definition:** 1 iff current transaction_type is cash_out.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 4. `wallet_count_1h_inclusive`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** count of subject-wallet events in [T-1h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 5. `wallet_value_24h_inclusive`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** sum of subject-wallet amounts in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 6. `wallet_count_utc_day_inclusive`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** count of subject-wallet events since UTC midnight through T.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 7. `wallet_active_hours_utc_day`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** distinct UTC hour buckets for subject-wallet events since midnight through T.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current timestamp and entity endpoint only.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 8. `wallet_current_amount_cluster_share_7d`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** share of subject-wallet events in [T-7d,T] within 5% of current amount.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 9. `wallet_band_share_7d_inclusive`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** share of subject-wallet events in [T-7d,T] in 7000..10500 USD.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 10. `wallet_count_acceleration_1h`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** inclusive 1h count / max(1, prior-28d count / 672).
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 11. `receiver_unique_sources_24h_inclusive`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** distinct W2W senders to receiver in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 12. `receiver_inflow_count_24h_inclusive`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** W2W inflow count to receiver in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 13. `receiver_inflow_acceleration_24h`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** inclusive receiver inflow count / max(1, prior-28d inflow count / 28).
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 14. `sender_unique_destinations_24h_inclusive`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** distinct W2W receivers from sender in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 15. `sender_outflow_count_24h_inclusive`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** W2W outflow count from sender in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 16. `sender_outflow_acceleration_24h`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** inclusive sender outflow count / max(1, prior-28d count / 28).
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 17. `current_return_path_length`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** shortest simple prior path receiver to sender, 1..5 edges in 7d; zero otherwise.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only plus current endpoints`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 18. `current_return_amount_ratio`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** current amount / first-edge amount of selected prior return path; -1 when absent.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only plus current amount`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 19. `wallet_observed_onward_funding_share_24h`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** observed outward value after prior funding anchor / observed funding value.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current for outflow`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 20. `wallet_prior_funding_age_hours`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** hours from prior funding anchor to current outflow; -1 when absent.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only plus current timestamp`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 21. `agent_service_count_1h_inclusive`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** agent service-event count in [T-1h,T]; zero for direct W2W.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 22. `agent_service_acceleration_1h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** inclusive service count / max(1, preceding-28d service count / 672); -1 if coverage insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 23. `agent_wallet_growth_ratio_7d`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** recent inclusive distinct serviced wallets / max(1, median of four preceding 7d counts); -1 if insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 24. `agent_new_wallet_share_7d`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** recent serviced-wallet fraction absent from preceding-28d wallet union; -1 if insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 25. `agent_top2_count_share_24h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** top-two serviced-wallet service-event share in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 26. `agent_top2_share_change_24h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** inclusive top-two share minus preceding-28d top-two share; -1 if insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 27. `agent_cash_value_skew_24h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** (CashOut value-CashIn value)/(sum) in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 28. `agent_cash_count_skew_24h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** corresponding signed event-count skew in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 29. `agent_cash_value_skew_change`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** inclusive cash value skew minus preceding-28d cash value skew; -1 if insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 30. `wallet_history_coverage_days`

- **Behavioural domain / subject:** Coverage is the elapsed span from the first prior observed event for the subject entity to T, capped at 28 days. It uses no private activation or campaign metadata. No prior event gives 0.0; it is prior-only and is never an eligibility flag.
- **Mathematical definition:** partition-local subject-wallet observation span before T, capped at 28 days.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 31. `receiver_history_coverage_days`

- **Behavioural domain / subject:** Coverage is the elapsed span from the first prior observed event for the subject entity to T, capped at 28 days. It uses no private activation or campaign metadata. No prior event gives 0.0; it is prior-only and is never an eligibility flag.
- **Mathematical definition:** partition-local receiver observation span before T, capped at 28 days.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

### 32. `agent_history_coverage_days`

- **Behavioural domain / subject:** Coverage is the elapsed span from the first prior observed event for the subject entity to T, capped at 28 days. It uses no private activation or campaign metadata. No prior event gives 0.0; it is prior-only and is never an eligibility flag.
- **Mathematical definition:** partition-local agent observation span before T, capped at 28 days; zero without agent.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.
