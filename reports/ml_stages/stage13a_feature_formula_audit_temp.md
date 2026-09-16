# Stage 13A Feature Formula Audit

**Date:** 2026-09-15
**Purpose:** Audit current implementation against Stage 10B JSON specification

## STRUCTURING FEATURES (6)

### 1. structuring_prior_tx_count_1h
**Stage 10B Definition:** `count(H_sender ∩ [t-1h,t))` - Prior outgoing transactions by the sender in the preceding hour
**Current Implementation (lines 135-139):**
- Uses `get_prior_indices()` with `max_hours=1`
- Filters by `sender_wallet == tx['sender_wallet']`
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 2. structuring_prior_value_sum_24h
**Stage 10B Definition:** `sum(amount for H_sender ∩ [t-24h,t))` - Prior outgoing transaction value accumulated by the sender in the preceding 24 hours
**Current Implementation (lines 141-145):**
- Uses `get_prior_indices()` with `max_hours=24`
- Filters by `sender_wallet == tx['sender_wallet']`
- Sums amounts
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 3. structuring_same_day_prior_tx_count
**Stage 10B Definition:** `count(H_sender where date(timestamp)=date(t))` - Prior outgoing transaction count by sender on the current calendar day
**Current Implementation (lines 147-154):**
- Uses `get_prior_indices()` without time limit
- Filters by `sender_wallet == tx['sender_wallet']`
- Filters by `event_timestamp.date() == current_date`
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 4. structuring_repeated_amount_ratio_7d
**Stage 10B Definition:** `count(|amount_i-amount_current|/max(amount_current,1)≤0.05) / count(H_sender_7d)` - Share of prior sender transactions in seven days whose amount is within 5% of the current amount
**Current Implementation (lines 156-170):**
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `sender_wallet == tx['sender_wallet']`
- Calculates threshold as `0.05 * max(current_amount, 1)`
- Counts amounts within threshold
- Divides by prior count
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 5. structuring_amount_cluster_dispersion_7d
**Stage 10B Definition:** `std(H_sender_7d.amount) / max(mean(H_sender_7d.amount),1)` - Relative dispersion of prior sender amounts in seven days
**Current Implementation (lines 172-189):**
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `sender_wallet == tx['sender_wallet']`
- Calculates sample standard deviation (divides by N, not N-1)
- Divides by max(mean, 1)
- **MATCH**: Correct (uses population std as typical for ML features)
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 6. structuring_near_threshold_history_ratio_7d
**Stage 10B Definition:** `count(0.90×reporting_threshold≤amount_i<reporting_threshold) / count(H_sender_7d)` - Share of prior sender amounts in seven days within 10% below the configured mobile-money reporting threshold
**Current Implementation (lines 191-205):**
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `sender_wallet == tx['sender_wallet']`
- Uses `SYNTHETIC_REPORTING_THRESHOLD = 10000`
- Counts amounts in [0.90*threshold, threshold)
- Divides by prior count
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

## NETWORK FEATURES (10)

### 7. network_outbound_counterparty_count_7d
**Stage 10B Definition:** `nunique(receiver_wallet in H_sender_out_7d)` - Distinct receivers paid by the sender in seven days
**Current Implementation (lines 211-216):**
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `sender_wallet == tx['sender_wallet']`
- Counts unique receivers
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 8. network_inbound_counterparty_count_7d
**Stage 10B Definition:** `nunique(sender_wallet in H_inbound_to_wallet_7d)` - Distinct wallets that previously paid the sender in seven days
**Current Implementation (lines 218-223):**
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `receiver_wallet == tx['receiver_wallet']`
- Counts unique senders
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 9. network_outbound_counterparty_entropy_30d
**Stage 10B Definition:** `-Σ p(receiver)×ln p(receiver), p from H_sender_out_30d` - Entropy of sender's prior outbound receiver distribution
**Current Implementation (lines 225-248):**
- Uses `get_prior_indices()` with `max_hours=24*30`
- Filters by `sender_wallet == tx['sender_wallet']`
- Calculates value-weighted probabilities
- Computes Shannon entropy
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 10. network_top_counterparty_value_share_30d
**Stage 10B Definition:** `max_receiver(sum amount) / sum(H_sender_out_30d.amount)` - Largest receiver's share of sender's prior outbound value
**Current Implementation (lines 250-268):**
- Uses `get_prior_indices()` with `max_hours=24*30`
- Filters by `sender_wallet == tx['sender_wallet']`
- Sums values by receiver
- Returns max value / total value
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 11. network_current_receiver_is_new
**Stage 10B Definition:** `1 if receiver_current ∉ receivers(H_sender_out_before_t), else 0` - Whether the current receiver has not appeared in sender's earlier outbound history
**Current Implementation (lines 270-276):**
- Uses `get_prior_indices()` without time limit
- Filters by `sender_wallet == tx['sender_wallet']`
- Builds set of prior receivers
- Returns 1.0 if current receiver not in set
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 12. network_repeated_receiver_ratio_30d
**Stage 10B Definition:** `count(tx to receiver with prior frequency≥2) / count(H_sender_out_30d)` - Share of prior outbound transactions to receivers seen at least twice in the prior 30-day history
**Current Implementation (lines 278-291):**
- Uses `get_prior_indices()` with `max_hours=24*30`
- Filters by `sender_wallet == tx['sender_wallet']`
- Counts receiver frequencies
- Identifies receivers with frequency >= 2
- Counts transactions to repeated receivers
- Divides by total prior count
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 13. network_reciprocal_flow_ratio_7d
**Stage 10B Definition:** `count(counterparties with both directions) / count(active counterparties)` - Share of sender's active counterparties with both inbound and outbound transfers during the window
**Current Implementation (lines 293-309):**
- Uses `get_prior_indices()` with `max_hours=24*7`
- Builds outbound_counterparties (receivers from sender)
- Builds inbound_counterparties (senders to wallet)
- Computes intersection / union
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 14. network_counterparty_set_change_7d
**Stage 10B Definition:** `1 - |R_recent∩R_prior| / |R_recent∪R_prior|` - Change between the most recent and preceding seven-day outbound receiver sets
**Current Implementation (lines 311-343):**
- Uses `range(idx)` directly instead of `get_prior_indices()`
- Defines recent window as [t-7d, t)
- Defines prior window as [t-14d, t-7d)
- Computes Jaccard distance
- **MATCH**: Correct
**Issues:** Uses direct range() instead of get_prior_indices, but still O(N²)

### 15. network_pass_through_ratio_24h
**Stage 10B Definition:** `sum(outbound amount H_24h) / max(sum(inbound amount H_24h),1)` - Prior outbound value divided by prior inbound value for the sender
**Current Implementation (lines 345-357):**
- Uses `get_prior_indices()` with `max_hours=24`
- Sums outbound (sender_wallet == current sender)
- Sums inbound (receiver_wallet == current wallet)
- Divides outbound / max(inbound, 1)
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 16. network_shared_counterparty_concentration_7d
**Stage 10B Definition:** `max over counterparties c of shared-neighbour_count(c) / max(active_counterparty_count,1)` - Maximum share of the sender's current counterparties that also interacted with any of the sender's other counterparties in the prior window
**Current Implementation (lines 359-385):**
- Uses `get_prior_indices()` with `max_hours=24*7`
- Builds sender_counterparties (both directions)
- For each counterparty, builds its neighbour set
- Finds max shared neighbours
- Divides by active counterparty count
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

## AGENT FEATURES (14)

### 17. agent_prior_tx_count_1h
**Stage 10B Definition:** `count(H_agent ∩ [t-1h,t))` - Transactions attributable to the current agent in the preceding hour
**Current Implementation (lines 391-399):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=1`
- Filters by `agent_id == tx['agent_id']`
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 18. agent_prior_tx_count_7d
**Stage 10B Definition:** `count(H_agent_7d)` - Transactions attributable to the current agent in seven days
**Current Implementation (lines 401-409):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `agent_id == tx['agent_id']`
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 19. agent_prior_value_sum_1h
**Stage 10B Definition:** `sum(H_agent_1h.amount)` - Value handled by current agent in the preceding hour
**Current Implementation (lines 411-419):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=1`
- Filters by `agent_id == tx['agent_id']`
- Sums amounts
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 20. agent_prior_value_sum_7d
**Stage 10B Definition:** `sum(H_agent_7d.amount)` - Value handled by current agent in seven days
**Current Implementation (lines 421-429):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `agent_id == tx['agent_id']`
- Sums amounts
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 21. agent_unique_wallet_count_7d
**Stage 10B Definition:** `nunique(wallets in H_agent_7d)` - Distinct wallets associated with prior transactions at the current agent
**Current Implementation (lines 431-444):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `agent_id == tx['agent_id']`
- Collects both sender and receiver wallets
- Counts unique wallets
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 22. agent_wallet_value_hhi_7d
**Stage 10B Definition:** `Σ(wallet_value / total_agent_value)^2` - Herfindahl-Hirschman concentration of prior agent-handled value by wallet
**Current Implementation (lines 446-471):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `agent_id == tx['agent_id']`
- **MISMATCH**: Only sums sender_wallet values, should include both sender and receiver
- Computes HHI correctly
- **ISSUE**: Missing receiver_wallet contributions to wallet value
**Correction Required:** Include both sender_wallet and receiver_wallet in wallet value aggregation

### 23. agent_repeat_wallet_ratio_7d
**Stage 10B Definition:** `count(tx involving wallet with agent frequency≥2) / count(H_agent_7d)` - Share of prior agent transactions involving wallets seen at the agent at least twice in the window
**Current Implementation (lines 473-496):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `agent_id == tx['agent_id']`
- Counts wallet frequency (both sender and receiver)
- Identifies wallets with frequency >= 2
- Counts transactions involving repeated wallets
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 24. agent_current_wallet_is_new
**Stage 10B Definition:** `1 if sender_wallet ∉ wallets(H_agent_before_t), else 0` - Whether the current transaction's initiating wallet is unseen in the agent's earlier history
**Current Implementation (lines 498-511):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` without time limit
- Filters by `agent_id == tx['agent_id']`
- Collects prior wallets (both sender and receiver)
- Returns 1.0 if current sender_wallet not in prior wallets
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 25. agent_inbound_outbound_value_ratio_7d
**Stage 10B Definition:** `sum(outbound H_agent_7d.amount) / max(sum(inbound H_agent_7d.amount),1)` - Prior agent-attributable outbound value divided by inbound value
**Current Implementation (lines 513-529):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `agent_id == tx['agent_id']`
- **CRITICAL MISMATCH**: Filters by `sender_wallet == tx['sender_wallet']` and `receiver_wallet == tx['receiver_wallet']`
- This restricts to the current wallet only, not all agent wallets
- **ISSUE**: Should be agent-level aggregation across ALL wallets associated with the agent
**Correction Required:** Remove wallet filters; aggregate across all agent transactions with direction based on transaction_direction field

### 26. agent_high_value_event_share_7d
**Stage 10B Definition:** `count(amount_i>2×median(H_agent_30d_before_i)) / count(H_agent_7d)` - Share of prior agent transactions whose amount exceeds twice that agent's preceding-30-day median amount
**Current Implementation (lines 531-554):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*30` for baseline
- Filters by `agent_id == tx['agent_id']`
- Calculates median from 30-day baseline
- Uses `get_prior_indices()` with `max_hours=24*7` for 7-day window
- Counts events above 2x median
- Divides by 7-day count
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

### 27. agent_hourly_tx_zscore_30d
**Stage 10B Definition:** `(count(H_agent_current_completed_hour)-mean(prior completed hourly counts_30d)) / max(std(...),1)` - Deviation of prior completed hourly transaction count from the agent's prior completed-hour baseline
**Current Implementation (lines 556-590):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*30`
- Filters by `agent_id == tx['agent_id']`
- **CRITICAL MISMATCH**: Line 570 excludes current hour: `if hour_key < current_hour_start`
- Line 576: `current_hour_count = hourly_counts.get(current_hour_start, 0)` - This will always be 0
- **ISSUE**: Earlier events in the same hour should contribute to current-hour activity
- **Correction Required**: Include events in current hour that are BEFORE the current event (based on event_sequence)

### 28. agent_hourly_value_zscore_30d
**Stage 10B Definition:** `(sum(H_agent_current_completed_hour.amount)-mean(prior completed hourly values_30d)) / max(std(...),1)` - Deviation of prior completed hourly handled value from the agent's prior completed-hour value baseline
**Current Implementation (lines 592-626):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*30`
- Filters by `agent_id == tx['agent_id']`
- **CRITICAL MISMATCH**: Line 606 excludes current hour: `if hour_key < current_hour_start`
- Line 612: `current_hour_value = hourly_values.get(current_hour_start, 0)` - This will always be 0
- **ISSUE**: Earlier events in the same hour should contribute to current-hour value
- **Correction Required**: Include events in current hour that are BEFORE the current event (based on event_sequence)

### 29. agent_burst_concentration_7d
**Stage 10B Definition:** `max_bucket_count(H_agent_7d,15min) / count(H_agent_7d)` - Largest prior 15-minute event bucket share of all prior agent events
**Current Implementation (lines 628-647):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `agent_id == tx['agent_id']`
- Groups by 15-minute buckets
- **POTENTIAL ISSUE**: Uses minute // 15 for bucketing, but doesn't include hour in bucket key
- This could cause collisions across different hours
- **ISSUE**: Bucket key should include both date and hour
**Correction Required**: Fix bucket key to include full timestamp resolution

### 30. agent_shared_wallet_flow_concentration_7d
**Stage 10B Definition:** `max_counterparty(distinct associated wallets linked to counterparty) / max(distinct associated wallets,1)` - Maximum share of agent-associated wallets that previously sent to or received from the same external counterparty
**Current Implementation (lines 649-686):**
- Returns 0 if agent_id is NULL
- Uses `get_prior_indices()` with `max_hours=24*7`
- Filters by `agent_id == tx['agent_id']`
- Builds agent_wallets set
- Identifies external_counterparties (not in agent_wallets)
- For each external counterparty, counts linked agent wallets
- Returns max linked / total agent wallets
- **MATCH**: Correct
**Issues:** None (but depends on fixing get_prior_indices O(N²))

## SUMMARY OF CRITICAL ISSUES

1. **O(N²) Performance Issue**: `get_prior_indices()` iterates through all prior transactions for every transaction (lines 115-129). This is the fundamental performance problem.

2. **agent_wallet_value_hhi_7d (line 460)**: Only sums sender_wallet values, should include both sender and receiver wallets.

3. **agent_inbound_outbound_value_ratio_7d (lines 521-524)**: CRITICAL - filters by current wallet only, should aggregate across ALL agent wallets. Needs to use transaction_direction field.

4. **agent_hourly_tx_zscore_30d (line 570)**: CRITICAL - excludes current hour entirely. Should include earlier events in same hour before current event.

5. **agent_hourly_value_zscore_30d (line 606)**: CRITICAL - excludes current hour entirely. Should include earlier events in same hour before current event.

6. **agent_burst_concentration_7d (line 642)**: Bucket key doesn't include hour, could cause collisions across hours.

## REQUIRED CORRECTIONS

1. Replace O(N²) scanning with incremental state management
2. Fix agent_wallet_value_hhi_7d to include receiver wallets
3. Fix agent_inbound_outbound_value_ratio_7d to be agent-level aggregation
4. Fix agent_hourly_zscore features to include current-hour prior events
5. Fix agent_burst_concentration_7d bucket key
