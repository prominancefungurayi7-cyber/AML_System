# Stage 5 Database & Mobile-Money Data-Model Audit and Design Report

**Date:** September 14, 2026  
**Scope:** Database Architecture Audit and Future Data-Model Design for EcoCash-style Mobile-Money AML System  
**Status:** ✅ COMPLETED  
**Type:** AUDIT AND DESIGN ONLY (NO IMPLEMENTATION)

---

## 1. Stage 5 Objective

Audit the existing database and backend data model to determine whether it can properly support the approved EcoCash-style mobile-money AML system. The audit identifies what data already exists, what mobile-money data the existing system can represent, what data is missing, and what minimum schema changes will be required to support the three approved AML detection dimensions: Structuring, Wallet/Transaction Network Behaviour, and Agent Behaviour.

**IMPORTANT:** This is an audit and design stage only. No schema changes were implemented.

---

## 2. Database Architecture Audited

### Files Inspected
- `database.py` - Database schema definition and adapter layer
- `users.py` - User management and account operations
- `transactions.py` - Transaction processing and retrieval
- `alerts.py` - Alert management and creation
- `reports.py` - SAR/CTR report generation
- `aml_rules.py` - AML rule definitions (inspected for data usage)
- `transaction_simulation.py` - Transaction simulation (inspected for data generation)

### Database Engine Support
The system supports three database engines:
- SQLite (default for development)
- MySQL
- PostgreSQL

Schema DDL is dynamically generated based on the database URL via `get_schema_sql()` in `database.py`.

### No Migration Files
No migration files were found in the repository. Schema is defined inline in `database.py` and created on application startup.

---

## 3. Current Tables and Relationships

### Table 1: users

**Purpose:** Application user accounts (serves as both application user and wallet holder)

**Primary Key:** `id` (auto-increment/identity)

**Important Columns:**
- `id` - Primary key
- `username` - Application login username (UNIQUE, NOT NULL)
- `password_hash` - Hashed password (NOT NULL)
- `account_number` - Wallet/account identifier (UNIQUE, NOT NULL)
- `id_number` - Zimbabwe ID number format (nullable)
- `email` - Email address (nullable)
- `role` - User role: 'customer', 'admin', 'compliance' (default: 'customer')
- `balance` - Account balance (REAL, default: 0.0)
- `kyc_status` - KYC status (default: 'pending')
- `risk_rating` - Customer risk rating (default: 'standard')
- `wealth_segment` - Wealth segment (default: 'average')
- `pep_flag` - Politically Exposed Person flag (INTEGER, default: 0)
- `created_at` - Account creation timestamp
- `last_login` - Last login timestamp (nullable)

**Relationships:**
- Referenced by `transactions.sender_account` (FK)
- Referenced by `transactions.receiver_account` (FK)
- Referenced by `alerts.account_number` (FK)
- Referenced by `behavioral_profiles.account_number` (FK)
- Referenced by `sar_reports.account_number` (no FK, but referenced)
- Referenced by `ctr_reports.account_number` (no FK, but referenced)

**Actively Used:** Yes - core table for authentication and wallet operations

**AML Relevance:** High - represents wallet holders and their risk profile

---

### Table 2: transactions

**Purpose:** Transaction records for all wallet-to-wallet transfers, cash-ins, and cash-outs

**Primary Key:** `id` (auto-increment/identity)

**Important Columns:**
- `id` - Primary key
- `sender_account` - Sender wallet identifier (NOT NULL, FK to users.account_number)
- `receiver_account` - Receiver wallet identifier (NOT NULL, FK to users.account_number)
- `amount` - Transaction amount (REAL, NOT NULL)
- `transaction_type` - Type: 'deposit', 'withdraw', 'transfer' (NOT NULL)
- `channel` - Channel: 'online', 'mobile', 'atm', 'branch', 'card', 'ach', 'swift' (default: 'online')
- `description` - Transaction description (nullable)
- `timestamp` - Transaction timestamp (default: CURRENT_TIMESTAMP)
- `risk_level` - Transaction risk level: 'normal', 'low', 'suspicious', 'high_risk', 'critical' (default: 'normal')
- `risk_score` - Risk score (REAL, default: 0.0)
- `rule_level` - Rule-based risk level (default: 'normal')
- `rule_score` - Rule-based risk score (REAL, default: 0.0)
- `ai_risk_level` - AI-predicted risk level (nullable)
- `ai_confidence` - AI prediction confidence (REAL, nullable)
- `generated_label` - Synthetic label for training data (nullable)
- `scenario_reason` - Simulation scenario reason (nullable)
- `destination_country` - Destination country code (default: 'ZW')
- `ctr_required` - CTR filing requirement flag (INTEGER, default: 0)
- `sar_required` - SAR filing requirement flag (INTEGER, default: 0)

**Indexes:**
- `idx_transactions_sender` on sender_account
- `idx_transactions_receiver` on receiver_account
- `idx_transactions_timestamp` on timestamp

**Relationships:**
- References `users.account_number` as sender (FK)
- References `users.account_number` as receiver (FK)
- Referenced by `alerts.transaction_id` (FK)
- Referenced by `sar_reports.transaction_id` (FK)

**Actively Used:** Yes - core transaction table

**AML Relevance:** Critical - primary data source for all AML analysis

---

### Table 3: alerts

**Purpose:** AML alerts generated for suspicious transactions

**Primary Key:** `id` (auto-increment/identity)

**Important Columns:**
- `id` - Primary key
- `transaction_id` - Associated transaction ID (FK to transactions.id)
- `account_number` - Wallet identifier (NOT NULL)
- `risk_score` - Alert risk score (REAL, NOT NULL)
- `risk_level` - Alert risk level (NOT NULL)
- `reason` - Alert reason (LONGTEXT)
- `rules_triggered` - JSON string of triggered rules (TEXT)
- `status` - Alert status: 'open', 'investigating', 'resolved', 'closed' (default: 'open')
- `assigned_to` - Assigned analyst username (nullable)
- `resolved_by` - Resolving analyst username (nullable)
- `resolved_at` - Resolution timestamp (nullable)
- `timestamp` - Alert creation timestamp (default: CURRENT_TIMESTAMP)

**Indexes:**
- `idx_alerts_account` on account_number
- `idx_alerts_status` on status

**Relationships:**
- References `transactions.id` (FK)
- References `users.account_number` (no FK, but referenced)

**Actively Used:** Yes - alert management

**AML Relevance:** High - stores AML investigation records

---

### Table 4: behavioral_profiles

**Purpose:** Behavioral profile data per wallet

**Primary Key:** `id` (auto-increment/identity)

**Important Columns:**
- `id` - Primary key
- `account_number` - Wallet identifier (UNIQUE, NOT NULL, FK to users.account_number)
- `profile_data` - Profile data (LONGTEXT, JSON format)
- `last_updated` - Last update timestamp (nullable)
- `total_transactions` - Total transaction count (INTEGER, default: 0)

**Relationships:**
- References `users.account_number` (FK)

**Actively Used:** Yes - behavioral profiling

**AML Relevance:** Medium - stores derived behavioral features

---

### Table 5: sar_reports

**Purpose:** Suspicious Activity Reports

**Primary Key:** `id` (auto-increment/identity)

**Important Columns:**
- `id` - Primary key
- `reference_number` - SAR reference number (UNIQUE, NOT NULL)
- `transaction_id` - Associated transaction ID (FK to transactions.id)
- `account_number` - Wallet identifier (NOT NULL)
- `filing_reason` - Filing reason (LONGTEXT)
- `status` - Report status (default: 'filed')
- `filed_by` - Filing user (nullable)
- `filed_at` - Filing timestamp (default: CURRENT_TIMESTAMP)

**Relationships:**
- References `transactions.id` (FK)
- References `users.account_number` (no FK, but referenced)

**Actively Used:** Yes - regulatory reporting

**AML Relevance:** High - regulatory compliance records

---

### Table 6: ctr_reports

**Purpose:** Currency Transaction Reports

**Primary Key:** `id` (auto-increment/identity)

**Important Columns:**
- `id` - Primary key
- `reference_number` - CTR reference number (UNIQUE, NOT NULL)
- `account_number` - Wallet identifier (NOT NULL)
- `total_amount` - Total amount for CTR (REAL, NOT NULL)
- `transaction_count` - Number of transactions (INTEGER, default: 1)
- `filing_date` - Filing date (DATE)
- `status` - Report status (default: 'filed')
- `filed_by` - Filing user (nullable)
- `filed_at` - Filing timestamp (default: CURRENT_TIMESTAMP)

**Relationships:**
- References `users.account_number` (no FK, but referenced)

**Actively Used:** Yes - regulatory reporting

**AML Relevance:** High - regulatory compliance records

---

### Table 7: system_activity_log

**Purpose:** System activity audit trail

**Primary Key:** `id` (auto-increment/identity)

**Important Columns:**
- `id` - Primary key
- `user_id` - User identifier (nullable)
- `action` - Action performed (NOT NULL)
- `details` - Action details (LONGTEXT)
- `timestamp` - Timestamp (default: CURRENT_TIMESTAMP)
- `ip_address` - IP address (nullable)

**Indexes:**
- `idx_activity_user` on user_id

**Actively Used:** Yes - audit logging

**AML Relevance:** Low - audit trail only

---

### Table 8: activity_log

**Purpose:** General activity logging

**Primary Key:** `id` (auto-increment/identity)

**Important Columns:**
- `id` - Primary key
- `actor` - Actor identifier (nullable)
- `action` - Action performed (NOT NULL)
- `detail` - Action detail (LONGTEXT)
- `ip_address` - IP address (nullable)
- `timestamp` - Timestamp (default: CURRENT_TIMESTAMP)

**Indexes:**
- `idx_activity_log_actor` on actor

**Actively Used:** Yes - activity logging

**AML Relevance:** Low - audit trail only

---

### Table 9: watchlist

**Purpose:** Watchlist entries for suspicious entities

**Primary Key:** `id` (auto-increment/identity)

**Important Columns:**
- `id` - Primary key
- `name` - Entity name (NOT NULL)
- `id_number` - ID number (nullable)
- `account_number` - Account/wallet number (nullable)
- `list_type` - List type (NOT NULL)
- `reason` - Watchlist reason (LONGTEXT)
- `added_by` - Adding user (nullable)
- `added_at` - Addition timestamp (default: CURRENT_TIMESTAMP)

**Indexes:**
- `idx_watchlist_type` on list_type
- `idx_watchlist_id_number` on id_number

**Actively Used:** Yes - watchlist management

**AML Relevance:** Medium - screening against known suspicious entities

---

## 4. Current Wallet / Account Representation

### Wallet Identifier
The current system uses `account_number` in the `users` table as the wallet identifier.

**Findings:**
- `account_number` is a TEXT field with UNIQUE constraint
- It is used as the foreign key reference in `transactions.sender_account` and `transactions.receiver_account`
- It is referenced in `alerts.account_number`, `behavioral_profiles.account_number`, `sar_reports.account_number`, and `ctr_reports.account_number`
- The field is currently named "account_number" but functionally serves as the wallet identifier

### Wallet Holder Representation
The `users` table represents both:
1. Application user (authentication credentials: username, password_hash)
2. Wallet holder (wallet data: account_number, balance, kyc_status, risk_rating, wealth_segment, pep_flag)

**Findings:**
- One user record = one wallet
- No separate "wallet holder" concept exists
- No support for one holder having multiple wallets
- No support for wallet hierarchy or wallet groups
- The `role` field distinguishes between 'customer', 'admin', and 'compliance' users

### Wallet Status
**Findings:**
- No explicit wallet status field (active, suspended, closed, etc.)
- Balance is tracked in `users.balance`
- KYC status is tracked in `users.kyc_status`
- Risk rating is tracked in `users.risk_rating`
- No wallet creation/activation timestamp separate from `users.created_at`

### Assessment
**Current Representation:** The existing `account_number` in the `users` table is sufficient to represent a wallet identifier for the current system scope.

**Future Consideration:** A separate `wallets` table may be beneficial if:
- One holder needs multiple wallets
- Wallet-specific metadata beyond what's in `users` is needed
- Wallet lifecycle management (activation, suspension, closure) becomes complex

**Recommendation:** For the approved Stage 6 scope, the existing `account_number` in `users` is sufficient. A separate `wallets` table is NOT required at this stage.

---

## 5. Transaction Data Audit

### Transaction Identification
**Findings:**
- Each transaction has a unique `id` (primary key)
- Each transaction has `sender_account` and `receiver_account` (wallet identifiers)
- Each transaction has `amount` (REAL)
- Each transaction has `timestamp` (TIMESTAMP)

### Transaction Type
**Findings:**
- `transaction_type` field stores: 'deposit', 'withdraw', 'transfer'
- These map to mobile-money concepts: Cash-In, Cash-Out, Wallet-to-Wallet Transfer
- No other transaction types exist

### Transaction Channel
**Findings:**
- `channel` field stores: 'online', 'mobile', 'atm', 'branch', 'card', 'ach', 'swift'
- No agent-specific channel exists
- Channel is generic and does not identify specific agents

### Transaction Direction
**Findings:**
- Direction is implied by `transaction_type`:
  - 'deposit' = cash-in (external to wallet)
  - 'withdraw' = cash-out (wallet to external)
  - 'transfer' = wallet-to-wallet
- No explicit direction field exists

### Transaction Status
**Findings:**
- No explicit transaction status field (pending, completed, failed, etc.)
- Transactions are assumed completed when inserted
- No transaction lifecycle tracking

### Agent Information
**Findings:**
- **MISSING:** No agent field in transactions table
- **MISSING:** No agent ID field
- **MISSING:** No agent location field
- Channel field is generic and does not identify specific agents

### Location Information
**Findings:**
- `destination_country` exists (default: 'ZW')
- **MISSING:** No transaction location field
- **MISSING:** No branch/terminal location
- **MISSING:** No geographic coordinates
- **MISSING:** No city/region fields

### Risk Information
**Findings:**
- `risk_level` - Transaction risk level
- `risk_score` - Transaction risk score
- `rule_level` - Rule-based risk level
- `rule_score` - Rule-based risk score
- `ai_risk_level` - AI-predicted risk level (nullable)
- `ai_confidence` - AI prediction confidence (nullable)
- `generated_label` - Synthetic training label (nullable)
- `scenario_reason` - Simulation reason (nullable)

**Assessment:** Risk fields exist but some may cause data leakage in ML training (see Section 15).

---

## 6. Transaction History Capability

### Chronological Ordering
**Findings:**
- `timestamp` field exists in transactions table
- Index `idx_transactions_timestamp` exists
- Transactions can be ordered by timestamp
- Timestamps are in ISO format with timezone support

### Wallet-Level History
**Findings:**
- Query exists: `get_transactions_by_account(conn, account_number, limit=50)` in transactions.py
- Query retrieves both sender and receiver transactions: `WHERE sender_account=? OR receiver_account=?`
- Ordered by timestamp DESC
- Supports historical transaction retrieval per wallet

### Counterparty Tracking
**Findings:**
- `sender_account` and `receiver_account` fields exist
- Can identify all transactions where a wallet was sender
- Can identify all transactions where a wallet was receiver
- Can reconstruct counterparty relationships from transaction records

### Transaction Frequency
**Findings:**
- Can be derived from transaction count per wallet within time windows
- Timestamp field enables time-window calculations
- No pre-computed frequency metrics exist

### Transaction Amounts
**Findings:**
- `amount` field exists (REAL)
- Can calculate cumulative amounts per wallet
- Can calculate amounts within time windows
- No pre-computed amount metrics exist

### Assessment
**Transaction History Capability:** The existing transaction table contains sufficient raw data to reconstruct chronological transaction history for a wallet, including:
- Previous transactions (via timestamp ordering)
- Transaction frequency (derivable from count)
- Transaction amounts (stored directly)
- Transaction direction (derivable from transaction_type)
- Counterparties (from sender_account and receiver_account)
- Transaction timing (from timestamp)
- Transaction sequences (from timestamp ordering)

**Limitation:** No pre-computed historical metrics exist. All historical features must be calculated on-the-fly from raw transaction records.

---

## 7. Structuring Data Requirements

### Structuring Requirements vs Existing Data

| Requirement | Existing Data | Derivable? | Missing Data | Future Change Required? |
| ----------- | ------------- | ---------- | ------------ | ----------------------- |
| Repeated small transactions | amount, timestamp | Yes | None | No |
| Threshold-near transactions | amount | Yes | None | No |
| Cumulative short-window amounts | amount, timestamp | Yes | None | No |
| Transaction bursts | timestamp, amount | Yes | None | No |
| Repeated amounts | amount | Yes | None | No |
| Repeated transaction timing | timestamp | Yes | None | No |
| Repeated cash-in/cash-out patterns | transaction_type, timestamp, amount | Yes | None | No |
| Wallet-level transaction frequency | timestamp, account_number | Yes | None | No |
| Small cash-ins (<$500) | transaction_type='deposit', amount | Yes | None | No |
| CTR structuring (near $10,000) | amount | Yes | None | No |
| Half-CTR structuring (near $5,000) | amount | Yes | None | No |

### Assessment
**Structuring Data Capability:** The existing transaction table contains sufficient raw data to calculate all structuring-related features:
- All structuring patterns can be derived from `amount`, `timestamp`, `transaction_type`, and `account_number`
- No new fields are required for structuring analysis
- No schema changes are required for structuring detection

**Implementation Note:** Structuring analytics must be implemented in application logic (Python), not in the database schema. The raw data is already present.

---

## 8. Wallet / Transaction Network Data Requirements

### Network Requirements vs Existing Data

| Requirement | Existing Data | Derivable? | Missing Data | Future Change Required? |
| ----------- | ------------- | ---------- | ------------ | ----------------------- |
| Sender → receiver relationships | sender_account, receiver_account | Yes | None | No |
| Many-to-one relationships | sender_account, receiver_account | Yes | None | No |
| One-to-many relationships | sender_account, receiver_account | Yes | None | No |
| Repeated counterparties | sender_account, receiver_account, timestamp | Yes | None | No |
| Transaction paths | sender_account, receiver_account, timestamp | Yes | None | No |
| Transaction sequences | sender_account, receiver_account, timestamp | Yes | None | No |
| Wallet-to-wallet flows | sender_account, receiver_account, amount, timestamp | Yes | None | No |
| Potential funnel structures | sender_account, receiver_account, amount | Yes | None | No |
| Potential circular flows | sender_account, receiver_account, timestamp | Yes | None | No |

### Assessment
**Network Data Capability:** The existing transaction table contains sufficient raw data to reconstruct wallet relationships and transaction flows:
- All network patterns can be derived from `sender_account`, `receiver_account`, `amount`, and `timestamp`
- No new fields are required for network analysis
- No schema changes are required for network detection

**Implementation Note:** Network analytics must be implemented in application logic (Python) or with graph processing libraries, not in the database schema. The raw data is already present.

---

## 9. Agent Data Requirements

### Agent Requirements vs Existing Data

| Requirement | Existing Data | Derivable? | Missing Data | Future Change Required? |
| ----------- | ------------- | ---------- | ------------ | ----------------------- |
| Agent ID | None | No | agent_id | Yes - Critical |
| Agent name/code | None | No | agent_name | Yes - Critical |
| Agent location | None | No | agent_location | Yes - High |
| Agent region | None | No | agent_region | Yes - Medium |
| Transaction processed through agent | None | No | transaction.agent_id | Yes - Critical |
| Wallet-agent relationship | None | No | wallet-agent mapping | Yes - Critical |
| Agent transaction history | None | No | agent-specific queries | Yes - High |
| Multiple wallets using same agent | None | No | agent_id field | Yes - Critical |
| Transaction concentration by agent | None | No | agent_id field | Yes - Critical |
| Suspicious wallets sharing agent | None | No | agent_id field | Yes - Critical |
| Agent/location concentration | None | No | agent_location | Yes - High |
| Repeated wallet-agent relationships | None | No | agent_id field | Yes - Critical |
| Temporal agent activity | None | No | agent_id, timestamp | Yes - High |

### Assessment
**Agent Data Capability:** The existing database **does not** contain any agent representation:
- **MISSING:** No agent table
- **MISSING:** No agent fields in transactions table
- **MISSING:** No agent fields in users table
- **MISSING:** No agent location fields
- Channel field is generic and does not identify specific agents

**Critical Gap:** Agent behaviour detection (one of the three approved AML dimensions) cannot be implemented without agent data.

**Future Change Required:** Yes - Agent data model must be added to support the approved AML scope. This is a critical requirement for Stage 6.

---

## 10. Agent Location Requirements

### Location Requirements vs Existing Data

| Requirement | Existing Data | Derivable? | Missing Data | Future Change Required? |
| ----------- | ------------- | ---------- | ------------ | ----------------------- |
| Agent location | None | No | agent_location | Yes - High |
| Agent city | None | No | agent_city | Yes - Medium |
| Agent region | None | No | agent_region | Yes - Medium |
| Geographic coordinates | None | No | agent_lat, agent_lon | Yes - Low |
| Transaction location | None | No | transaction.location | Yes - Medium |
| Branch location | None | No | branch.location | Yes - Medium |

### Existing Location Data
- `destination_country` in transactions table (default: 'ZW')
- No other location fields exist

### Assessment
**Location Data Capability:** The existing database has minimal location information:
- Only country-level data exists (destination_country)
- No agent location data exists
- No transaction location data exists
- No geographic coordinates exist

**Future Change Required:** Yes - Agent location data must be added to support agent concentration analysis. This is a high-priority requirement for Stage 6.

---

## 11. Wallet Holder / Customer Relationships

### Current Relationship Model

The current system has a **single-table model**:

```
users table
├── Application user (username, password_hash, role)
└── Wallet holder (account_number, balance, kyc_status, risk_rating, wealth_segment, pep_flag)
```

**Findings:**
- No separate "wallet holder" concept
- Users table serves dual purpose: authentication + wallet holder
- One user = one wallet (1:1 relationship)
- No support for one holder having multiple wallets
- No support for wallet hierarchy or wallet groups

### Assessment
**Wallet Holder Representation:** The existing `users` table adequately represents wallet holders for the current system scope.

**Future Consideration:** A separate `wallet_holders` table may be beneficial if:
- Identity management (KYC) becomes complex
- One holder needs multiple wallets
- Wallet holder lifecycle becomes distinct from application user lifecycle

**Recommendation:** For the approved Stage 6 scope, the existing `users` table is sufficient. A separate `wallet_holders` table is NOT required at this stage.

---

## 12. Alert and AML Record Relationships

### Alert-Transaction Relationship
**Findings:**
- `alerts.transaction_id` references `transactions.id` (FK)
- `alerts.account_number` references wallet (no FK, but logical reference)
- One alert can be associated with one transaction
- One transaction can have at most one alert (enforced by application logic in alerts.py)

### Alert-Wallet Relationship
**Findings:**
- `alerts.account_number` identifies the wallet associated with the alert
- Alerts can be queried by account number via `get_alerts_by_account()`
- Alert status workflow: open → investigating → resolved/closed

### Alert Investigation Tracking
**Findings:**
- `alerts.status` tracks investigation status
- `alerts.assigned_to` tracks assigned analyst
- `alerts.resolved_by` tracks resolving analyst
- `alerts.resolved_at` tracks resolution timestamp
- `alerts.reason` stores alert reason (LONGTEXT)
- `alerts.rules_triggered` stores triggered rules (JSON)

### Assessment
**Alert Data Capability:** The existing alert table can identify:
- Transaction (via transaction_id)
- Wallet (via account_number)
- Risk level and score
- Alert status and investigation status
- Alert reason and triggered rules

**Future AML Evidence:** Future AML evidence (agent scores, network scores, structuring scores) can be associated with alerts by:
1. Adding new fields to alerts table (agent_score, network_score, structuring_score)
2. Storing evidence in `alerts.reason` or a new `evidence` field
3. Creating a separate `alert_evidence` table

**Recommendation:** The existing alert model is sufficient for current scope. Future AML dimensions can be added via new fields or a separate evidence table in Stage 6.

---

## 13. SAR/CTR Data Requirements

### SAR Data Structure
**Findings:**
- `sar_reports.transaction_id` references `transactions.id` (FK)
- `sar_reports.account_number` references wallet
- `sar_reports.reference_number` is a unique SAR reference
- `sar_reports.filing_reason` stores filing reason (LONGTEXT)
- `sar_reports.status` tracks report status
- `sar_reports.filed_by` and `sar_reports.filed_at` track filing metadata

### CTR Data Structure
**Findings:**
- `ctr_reports.account_number` references wallet
- `ctr_reports.reference_number` is a unique CTR reference
- `ctr_reports.total_amount` stores total amount for CTR
- `ctr_reports.transaction_count` stores number of transactions
- `ctr_reports.filing_date` stores filing date
- `ctr_reports.status` tracks report status
- `ctr_reports.filed_by` and `ctr_reports.filed_at` track filing metadata

### Assessment
**SAR/CTR Data Capability:** The existing SAR/CTR tables can represent mobile-money terminology without schema changes:
- `account_number` can represent wallet number (terminology only, no field change needed)
- Transaction fields used are compatible with mobile-money concepts
- No schema changes are required for SAR/CTR functionality

**Recommendation:** No schema changes required for SAR/CTR reporting. Terminology migration (Stage 4) already addressed docstring updates.

---

## 14. Temporal Safety Assessment

### Timestamp Availability
**Findings:**
- `transactions.timestamp` exists with ISO format and timezone support
- `alerts.timestamp` exists
- `users.created_at` and `users.last_login` exist
- All relevant tables have timestamp fields

### Chronological Ordering
**Findings:**
- Index `idx_transactions_timestamp` exists
- Transactions can be ordered by timestamp
- Historical transactions can be filtered to those before a given timestamp

### Temporal Feature Calculation
**Findings:**
- Historical transaction counts can be calculated with `WHERE timestamp < ?`
- Historical transaction amounts can be calculated with `WHERE timestamp < ?`
- Counterparty history can be calculated with `WHERE timestamp < ?`
- Frequency metrics can be calculated with time-window queries

### Assessment
**Temporal Safety:** The existing database design supports temporal-safe AML modelling:
- All historical features can be calculated using only information available before the prediction transaction
- Timestamp fields enable proper temporal separation
- No future-information leakage is inherent in the schema design

**Implementation Requirement:** Application logic must ensure that feature calculations use only historical data (timestamp < current transaction timestamp). The schema supports this, but implementation must enforce it.

---

## 15. Data Leakage Assessment

### Potential Data Leakage Fields

The following fields in the transactions table could leak labels or future risk decisions into ML training:

| Field | Type | Leakage Risk | Suitable as ML Input? | Reason |
| ----- | ---- | ------------ | ------------------- | ------ |
| risk_level | TEXT | HIGH | NO | Downstream risk decision |
| risk_score | REAL | HIGH | NO | Downstream risk decision |
| rule_level | TEXT | HIGH | NO | Downstream rule engine output |
| rule_score | REAL | HIGH | NO | Downstream rule engine output |
| ai_risk_level | TEXT | HIGH | NO | Downstream AI prediction |
| ai_confidence | REAL | HIGH | NO | Downstream AI confidence |
| generated_label | TEXT | HIGH | NO | Training label (ground truth) |
| scenario_reason | TEXT | MEDIUM | NO | Simulation metadata (synthetic only) |
| ctr_required | INTEGER | LOW | MAYBE | Regulatory flag (may be legitimate feature) |
| sar_required | INTEGER | LOW | MAYBE | Regulatory flag (may be legitimate feature) |

### Legitimate Raw Data Fields

The following fields are legitimate raw data suitable for ML input:

| Field | Type | Suitable as ML Input? | Reason |
| ----- | ---- | ------------------- | ------ |
| id | INTEGER | NO | Primary key (no semantic meaning) |
| sender_account | TEXT | YES | Wallet identifier |
| receiver_account | TEXT | YES | Wallet identifier |
| amount | REAL | YES | Transaction amount |
| transaction_type | TEXT | YES | Transaction type (deposit/withdraw/transfer) |
| channel | TEXT | YES | Transaction channel |
| description | TEXT | MAYBE | Transaction description (if available in production) |
| timestamp | TIMESTAMP | YES | Transaction timestamp |
| destination_country | TEXT | YES | Destination country |

### Assessment
**Data Leakage Risk:** The transactions table contains several fields that could leak labels or downstream decisions:
- `risk_level`, `risk_score`, `rule_level`, `rule_score` are downstream risk decisions
- `ai_risk_level`, `ai_confidence` are downstream AI predictions
- `generated_label` is the training label itself

**Recommendation:** When training ML models, exclude all leakage fields from input features. Use only legitimate raw data fields (sender_account, receiver_account, amount, transaction_type, channel, timestamp, destination_country).

---

## 16. Current Data vs Future Requirements Matrix

### Structuring Dimension

| Requirement | Current Status | Action Needed |
| ----------- | -------------- | ------------- |
| Repeated small transactions | Already supported | None |
| Threshold-near transactions | Already supported | None |
| Cumulative short-window amounts | Already supported | None |
| Transaction bursts | Already supported | None |
| Repeated amounts | Already supported | None |
| Repeated transaction timing | Already supported | None |
| Repeated cash-in/cash-out patterns | Already supported | None |
| Wallet-level transaction frequency | Already supported | None |

### Network Dimension

| Requirement | Current Status | Action Needed |
| ----------- | -------------- | ------------- |
| Sender → receiver relationships | Already supported | None |
| Many-to-one relationships | Already supported | None |
| One-to-many relationships | Already supported | None |
| Repeated counterparties | Already supported | None |
| Transaction paths | Already supported | None |
| Transaction sequences | Already supported | None |
| Wallet-to-wallet flows | Already supported | None |
| Potential funnel structures | Already supported | None |
| Potential circular flows | Already supported | None |

### Agent Dimension

| Requirement | Current Status | Action Needed |
| ----------- | -------------- | ------------- |
| Agent ID | MISSING | Add agent table and agent_id field |
| Agent name/code | MISSING | Add to agent table |
| Agent location | MISSING | Add to agent table |
| Agent region | MISSING | Add to agent table |
| Transaction processed through agent | MISSING | Add agent_id to transactions |
| Wallet-agent relationship | MISSING | Add wallet-agent mapping table |
| Agent transaction history | MISSING | Add agent-specific queries |
| Multiple wallets using same agent | MISSING | Add agent_id to transactions |
| Transaction concentration by agent | MISSING | Add agent_id to transactions |
| Suspicious wallets sharing agent | MISSING | Add agent_id to transactions |
| Agent/location concentration | MISSING | Add agent location fields |
| Repeated wallet-agent relationships | MISSING | Add agent_id to transactions |
| Temporal agent activity | MISSING | Add agent_id to transactions |

---

## 17. Proposed Schema Changes

### Schema Change Candidates

| Proposed Change | Why Needed | AML Dimension | Evidence | Priority | Implement Now? |
| --------------- | ---------- | ------------- | -------- | -------- | -------------- |
| Add agents table | Agent behaviour detection requires agent representation | Agent | Section 9 - Agent data completely missing | Critical | NO |
| Add agent_id to transactions | Link transactions to agents for agent behaviour analysis | Agent | Section 9 - Cannot track agent transactions without this | Critical | NO |
| Add agent_location to agents table | Agent concentration analysis requires location data | Agent | Section 10 - No location data exists | High | NO |
| Add agent_region to agents table | Regional agent analysis | Agent | Section 10 - No regional data exists | Medium | NO |
| Add wallet_agent_relationships table | Track which wallets use which agents | Agent | Section 9 - No wallet-agent mapping exists | High | NO |
| Add transaction.location field | Transaction location tracking | Agent | Section 10 - No transaction location exists | Medium | NO |
| Add alert.agent_score field | Store agent risk score in alert | Agent | Future agent AML evidence | Medium | NO |
| Add alert.network_score field | Store network risk score in alert | Network | Future network AML evidence | Medium | NO |
| Add alert.structuring_score field | Store structuring risk score in alert | Structuring | Future structuring AML evidence | Medium | NO |
| Rename account_number to wallet_number | Terminology clarity | All | Stage 4 terminology migration | Low | NO |

### Detailed Schema Proposals

#### Proposal 1: agents Table (CRITICAL)

```sql
CREATE TABLE agents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    agent_code TEXT UNIQUE NOT NULL,
    agent_name TEXT NOT NULL,
    location TEXT,
    region TEXT,
    city TEXT,
    latitude REAL,
    longitude REAL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Represent mobile-money agents for agent behaviour analysis

**Priority:** Critical - Required for Agent dimension AML detection

**Implement Now:** NO - Stage 5 is audit/design only

---

#### Proposal 2: Add agent_id to transactions Table (CRITICAL)

```sql
ALTER TABLE transactions ADD COLUMN agent_id BIGINT;
ALTER TABLE transactions ADD CONSTRAINT fk_agent FOREIGN KEY (agent_id) REFERENCES agents(id);
```

**Purpose:** Link each transaction to the agent that processed it

**Priority:** Critical - Required for agent behaviour analysis

**Implement Now:** NO - Stage 5 is audit/design only

---

#### Proposal 3: wallet_agent_relationships Table (HIGH)

```sql
CREATE TABLE wallet_agent_relationships (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    account_number TEXT NOT NULL,
    agent_id BIGINT NOT NULL,
    relationship_type TEXT DEFAULT 'primary',
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transaction_count INTEGER DEFAULT 0,
    FOREIGN KEY (account_number) REFERENCES users(account_number),
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    UNIQUE(account_number, agent_id)
);
```

**Purpose:** Track which wallets use which agents and the frequency of usage

**Priority:** High - Enables agent concentration analysis

**Implement Now:** NO - Stage 5 is audit/design only

---

#### Proposal 4: Add AML Score Fields to alerts Table (MEDIUM)

```sql
ALTER TABLE alerts ADD COLUMN agent_score REAL;
ALTER TABLE alerts ADD COLUMN network_score REAL;
ALTER TABLE alerts ADD COLUMN structuring_score REAL;
```

**Purpose:** Store dimension-specific AML scores in alerts for investigation

**Priority:** Medium - Enables evidence tracking for each AML dimension

**Implement Now:** NO - Stage 5 is audit/design only

---

#### Proposal 5: Add transaction.location Field (MEDIUM)

```sql
ALTER TABLE transactions ADD COLUMN location TEXT;
```

**Purpose:** Track transaction location (agent location or branch)

**Priority:** Medium - Enables location-based analysis

**Implement Now:** NO - Stage 5 is audit/design only

---

#### Proposal 6: Rename account_number to wallet_number (LOW)

```sql
-- This would require extensive migration across all tables
-- NOT RECOMMENDED at this stage
```

**Purpose:** Terminology clarity

**Priority:** Low - Terminology already addressed in Stage 4 (docstrings only)

**Implement Now:** NO - High risk, low benefit, terminology already migrated in documentation

---

## 18. Minimum Future Data Model

### Proposed Future Relationship Map

```
┌─────────────────┐
│   users         │
│   (wallet       │
│    holders)     │
└────────┬────────┘
         │ account_number
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│  transactions   │  │ behavioral_    │
│  ┌───────────┐  │  │  profiles      │
│  │ agent_id │──┼──┤                 │
│  └───────────┘  │  └─────────────────┘
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│     agents      │  │     alerts      │
│  ┌───────────┐  │  │  ┌───────────┐  │
│  │ location  │  │  │  │ agent_    │  │
│  │ region    │  │  │  │ score     │  │
│  │ city      │  │  │  │ network_  │  │
│  └───────────┘  │  │  │ score     │  │
└─────────────────┘  │  │ struct_   │  │
                     │  │ score     │  │
                     │  └───────────┘  │
                     └─────────────────┘
```

### Minimum Schema for Approved AML Scope

**Required for Agent Dimension:**
1. `agents` table - Agent representation
2. `transactions.agent_id` field - Link transactions to agents
3. `wallet_agent_relationships` table - Track wallet-agent usage patterns

**Optional but Recommended:**
4. `alerts.agent_score`, `alerts.network_score`, `alerts.structuring_score` - Dimension-specific scores
5. `transactions.location` field - Transaction location tracking

**Not Required:**
- Separate `wallets` table (existing `account_number` in `users` is sufficient)
- Separate `wallet_holders` table (existing `users` table is sufficient)
- Renaming `account_number` to `wallet_number` (high risk, low benefit)

---

## 19. Database Relationship Diagram

### Current System Relationship Map

```
┌─────────────────────────────────────────────────────────────┐
│                        users                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ id, username, password_hash, account_number,          │  │
│  │ id_number, email, role, balance, kyc_status,          │  │
│  │ risk_rating, wealth_segment, pep_flag,                 │  │
│  │ created_at, last_login                                │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │ account_number
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  transactions    │ │  alerts          │ │ behavioral_     │
│  ┌────────────┐  │ │  ┌────────────┐  │ │  profiles       │
│  │ sender_    │──┼─┼──│ transaction│  │ │  ┌────────────┐  │
│  │ account    │  │ │  │ _id        │  │ │  │ account_   │  │
│  │ receiver_  │  │ │  │ account_   │  │ │  │ number     │  │
│  │ account    │  │ │  │ number     │  │ │  └────────────┘  │
│  └────────────┘  │ │  └────────────┘  │ └──────────────────┘
└──────────────────┘ └──────────────────┘
          │                 │
          │                 │
          ▼                 ▼
┌──────────────────┐ ┌──────────────────┐
│  sar_reports     │ │  ctr_reports     │
│  ┌────────────┐  │ │  ┌────────────┐  │
│  │ transaction│  │ │  │ account_   │  │
│  │ _id        │  │ │  │ number     │  │
│  │ account_   │  │ │  └────────────┘  │
│  │ number     │  │ └──────────────────┘
│  └────────────┘  │
└──────────────────┘
```

### Proposed Future Relationship Map (NOT IMPLEMENTED)

```
┌─────────────────────────────────────────────────────────────┐
│                        users                                │
│  (wallet holders - existing table, no changes)             │
└───────────────────────────┬─────────────────────────────────┘
                            │ account_number
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  transactions    │ │  alerts          │ │ behavioral_     │
│  ┌────────────┐  │ │  ┌────────────┐  │ │  profiles       │
│  │ sender_    │  │ │  │ transaction│  │ │  (existing)     │
│  │ account    │  │ │  │ _id        │  │ │                  │
│  │ receiver_  │  │ │  │ account_   │  │ │                  │
│  │ account    │  │ │  │ number     │  │ │                  │
│  │ agent_id   │──┼─┼──│ agent_     │  │ │                  │
│  │ location   │  │ │  │ score     │  │ │                  │
│  └────────────┘  │ │  │ network_   │  │ │                  │
│         │        │ │  │ score     │  │ │                  │
│         │        │ │  │ struct_   │  │ │                  │
│         │        │ │  │ score     │  │ │                  │
│         │        │ │  └────────────┘  │ │                  │
│         │        │ └──────────────────┘ │                  │
│         │        │                      │                  │
│         ▼        │                      │                  │
│  ┌───────────────┐                      │                  │
│  │ agents        │                      │                  │
│  │ (NEW TABLE)   │                      │                  │
│  │ ┌───────────┐ │                      │                  │
│  │ │ agent_    │ │                      │                  │
│  │ │ code      │ │                      │                  │
│  │ │ location  │ │                      │                  │
│  │ │ region    │ │                      │                  │
│  │ │ city      │ │                      │                  │
│  │ └───────────┘ │                      │                  │
│  └───────────────┘                      │                  │
│         │                               │                  │
│         │                               │                  │
│         ▼                               │                  │
│  ┌───────────────┐                      │                  │
│  │ wallet_agent_  │                      │                  │
│  │ relationships  │                      │                  │
│  │ (NEW TABLE)    │                      │                  │
│  └───────────────┘                      │                  │
└──────────────────────────────────────────┘
```

**NOTE:** The proposed future relationship map is NOT IMPLEMENTED. It is a design proposal for Stage 6.

---

## 20. AI Compatibility Assessment

### Structuring AI Data Requirements

| Required Data | Exists? | Location | Access Method |
| ------------- | ------- | -------- | ------------- |
| amount | YES | transactions.amount | Direct field access |
| timestamp | YES | transactions.timestamp | Direct field access |
| transaction_type | YES | transactions.transaction_type | Direct field access |
| wallet | YES | transactions.sender_account / receiver_account | Direct field access |
| prior transaction history | YES | transactions table | Query WHERE timestamp < current |
| transaction frequency | DERIVABLE | transactions table | COUNT WHERE timestamp < current |
| cumulative amounts | DERIVABLE | transactions table | SUM WHERE timestamp < current |

**Assessment:** All structuring AI data requirements are met by the existing schema. No schema changes required for structuring AI features.

---

### Network AI Data Requirements

| Required Data | Exists? | Location | Access Method |
| ------------- | ------- | -------- | ------------- |
| sender wallet | YES | transactions.sender_account | Direct field access |
| receiver wallet | YES | transactions.receiver_account | Direct field access |
| amount | YES | transactions.amount | Direct field access |
| timestamp | YES | transactions.timestamp | Direct field access |
| transaction sequence | DERIVABLE | transactions table | ORDER BY timestamp |
| counterparty history | DERIVABLE | transactions table | Query WHERE sender_account OR receiver_account |

**Assessment:** All network AI data requirements are met by the existing schema. No schema changes required for network AI features.

---

### Agent AI Data Requirements

| Required Data | Exists? | Location | Access Method |
| ------------- | ------- | -------- | ------------- |
| agent | NO | MISSING | N/A |
| wallet | YES | transactions.sender_account / receiver_account | Direct field access |
| transaction | YES | transactions table | Direct field access |
| timestamp | YES | transactions.timestamp | Direct field access |
| amount | YES | transactions.amount | Direct field access |
| agent location | NO | MISSING | N/A |

**Assessment:** Agent AI data requirements are NOT met. Agent data is completely missing from the schema. Schema changes are REQUIRED for agent AI features.

---

### Overall AI Compatibility

| AML Dimension | Data Available | Schema Changes Required? |
| ------------- | -------------- | ------------------------ |
| Structuring | YES | NO |
| Network | YES | NO |
| Agent | NO | YES (Critical) |

**Assessment:** The existing database can support structuring and network AI features without schema changes. Agent AI features require critical schema additions (agents table, agent_id field in transactions).

---

## 21. Tests Performed

### A. Application Startup Test

**Command:** `python server.py`  
**Result:** ✅ PASSED
- Flask web server started successfully on http://127.0.0.1:5000
- No errors related to database schema
- Server started with normal warnings (Redis connection timeout - expected in dev environment)
- No schema modifications occurred during startup

### B. Database Integrity Test

**Verification:** Git diff inspection  
**Result:** ✅ PASSED
- No database schema files were modified
- No migration files were created or modified
- No tables were added or removed
- No columns were added or removed
- No indexes were added or removed
- No constraints were added or removed
- database.py was not modified

### C. Transaction Compatibility Test

**Verification:** Code inspection of transactions.py  
**Result:** ✅ PASSED
- Transaction creation logic unchanged
- Transaction retrieval logic unchanged
- Transaction types remain unchanged ('deposit', 'withdraw', 'transfer')
- Existing transaction data remains readable
- No transaction processing logic was modified

### D. AI Protection Test

**Verification:** Git diff inspection and ai_core.py inspection  
**Result:** ✅ PASSED
- `ai_core.py` was not modified
- No ML files (.pkl, .joblib) were found or modified
- No datasets were modified
- No model artifacts were modified
- No features were changed
- No labels were changed
- No thresholds were changed

### E. API Protection Test

**Verification:** Git diff inspection and server.py inspection  
**Result:** ✅ PASSED
- No server.py endpoint changes
- No API contract modifications
- No request/response structure changes
- No new endpoints added
- No existing endpoints removed

### F. Git Verification

**Commands:** `git status`, `git diff`  
**Result:** ✅ PASSED
- Git status shows only Stage 4 changes (aml_rules.py, reports.py, transaction_simulation.py)
- No new files were added in Stage 5
- No implementation changes were made
- No schema changes were made
- Stage 5 was strictly audit and design only

---

## 22. Git Diff Review

**Git Status:**
```
Changes not staged for commit:
  modified:   aml_rules.py
  modified:   reports.py
  modified:   transaction_simulation.py
```

**Git Diff Summary:**
- Only Stage 4 changes are present (documentation/terminology only)
- No Stage 5 implementation changes are present
- No database schema changes are present
- No new tables or columns were added
- No AI model changes are present
- No API contract changes are present

**Confirmation:** Stage 5 was strictly audit and design only. No implementation changes were made. The git diff confirms that only Stage 4 documentation changes remain in the working directory.

---

## 23. Stage 6 Dependencies

### Critical Dependencies for Stage 6

**Agent Data Model Implementation:**
1. Create `agents` table with agent_code, agent_name, location, region, city, latitude, longitude
2. Add `agent_id` field to `transactions` table with foreign key to agents
3. Create `wallet_agent_relationships` table to track wallet-agent usage patterns
4. Implement agent-specific queries and analytics
5. Add agent score fields to alerts table (optional but recommended)

**Agent Location Implementation:**
1. Populate agent location data (city, region, coordinates)
2. Implement agent concentration analysis
3. Implement regional agent analysis

**Alert Evidence Enhancement:**
1. Add `agent_score`, `network_score`, `structuring_score` fields to alerts table
2. Implement dimension-specific score calculation
3. Update alert display to show dimension-specific evidence

### Non-Critical Dependencies

**Transaction Location:**
- Add `location` field to transactions table (optional)
- Implement transaction location tracking (optional)

**Terminology Cleanup:**
- Consider renaming `account_number` to `wallet_number` (low priority, high risk)
- This is NOT required for Stage 6

---

## 24. Outstanding Questions / Risks

### Questions

1. **Agent Data Source:** Where will agent data come from? Is there an existing agent registry or will agents be manually created?

2. **Agent Location Data:** What geographic granularity is required for agent location analysis? City level? Region level? GPS coordinates?

3. **Wallet-Agent Mapping:** How will wallet-agent relationships be established? Will this be based on transaction history or explicit registration?

4. **Agent Status:** Should agents have status tracking (active, suspended, closed)? If so, what are the business rules?

5. **Transaction Location:** Should transaction location be tracked separately from agent location? For example, if a wallet uses an agent remotely?

### Risks

1. **Agent Data Availability:** If agent data is not readily available, Stage 6 implementation may be delayed.

2. **Agent Location Accuracy:** If agent location data is incomplete or inaccurate, agent concentration analysis may be unreliable.

3. **Wallet-Agent Mapping Complexity:** If wallet-agent relationships are complex (e.g., wallets use multiple agents), the data model may need refinement.

4. **Performance Impact:** Adding agent_id foreign key to transactions table may impact query performance for large transaction volumes.

5. **Data Migration:** If the system has existing transaction data, backfilling agent_id for historical transactions may be challenging.

### Mitigation Strategies

1. **Agent Data Source:** Establish agent data source before Stage 6 implementation. Create agent registry or import from existing systems.

2. **Agent Location Accuracy:** Validate agent location data before using in analysis. Implement data quality checks.

3. **Wallet-Agent Mapping:** Start with simple mapping (primary agent per wallet) and evolve to complex mapping if needed.

4. **Performance Impact:** Test query performance with agent_id foreign key before production deployment. Add indexes if needed.

5. **Data Migration:** Plan for historical data migration. If agent_id cannot be backfilled, mark historical transactions as agent_id = NULL.

---

## 25. Independent Re-Audit

### Structuring Dimension Verification

**Question:** Can the proposed raw data support future structuring features?

**Answer:** YES
- All structuring patterns can be derived from existing transaction data
- Amount, timestamp, transaction_type, and account_number are sufficient
- No schema changes required
- Temporal safety is supported by timestamp field

**Verification:** ✅ PASSED

---

### Wallet/Transaction Network Dimension Verification

**Question:** Can the proposed raw data reconstruct wallet relationships and transaction flows?

**Answer:** YES
- Sender_account and receiver_account enable relationship reconstruction
- Timestamp enables sequence reconstruction
- Amount enables flow analysis
- No schema changes required
- Temporal safety is supported by timestamp field

**Verification:** ✅ PASSED

---

### Agent Behaviour Dimension Verification

**Question:** Can the proposed raw data connect wallets, transactions, agents, and agent locations?

**Answer:** NO (without proposed schema changes)
- Current schema has NO agent representation
- Current schema has NO agent fields in transactions
- Current schema has NO agent location data
- Proposed agents table and agent_id field are REQUIRED
- Proposed wallet_agent_relationships table is RECOMMENDED

**Verification:** ⚠️ CONDITIONAL - Requires proposed schema changes

---

### Temporal Safety Verification

**Question:** Does the design support temporal-safe AML modelling?

**Answer:** YES
- Timestamp fields exist in all relevant tables
- No future-information leakage is inherent in the schema
- Historical features can be calculated with WHERE timestamp < current
- Implementation must enforce temporal separation (schema supports it)

**Verification:** ✅ PASSED

---

### Data Leakage Verification

**Question:** Are there fields that could leak labels or future risk decisions?

**Answer:** YES (identified in Section 15)
- risk_level, risk_score, rule_level, rule_score are downstream decisions
- ai_risk_level, ai_confidence are downstream predictions
- generated_label is the training label
- These fields must be excluded from ML input features

**Verification:** ✅ PASSED (leakage identified and documented)

---

### Customer/Wallet Isolation Verification

**Question:** Can the design support customer/wallet isolation for ML evaluation?

**Answer:** YES
- account_number uniquely identifies each wallet
- Transactions can be filtered by account_number
- No cross-wallet data leakage in schema design
- Implementation must enforce wallet-level isolation

**Verification:** ✅ PASSED

---

### Agent Isolation Verification

**Question:** Can the proposed design support agent isolation for ML evaluation?

**Answer:** YES (with proposed schema changes)
- Proposed agent_id field enables agent-level filtering
- Proposed agents table enables agent-level analysis
- Implementation must enforce agent-level isolation

**Verification:** ✅ PASSED (with proposed schema)

---

### Reproducibility Verification

**Question:** Is the design reproducible?

**Answer:** YES
- All data is stored in relational database
- Timestamps enable temporal reproducibility
- Deterministic queries can be written
- No random data generation in schema

**Verification:** ✅ PASSED

---

### Auditability Verification

**Question:** Is the design auditable?

**Answer:** YES
- All tables have timestamps
- system_activity_log and activity_log track actions
- Foreign keys enable relationship tracing
- No data deletion mechanisms in schema (only updates)

**Verification:** ✅ PASSED

---

### Weaknesses Identified

1. **Agent Data Missing:** The current schema has NO agent representation. This is a critical gap for the approved Agent AML dimension.

2. **Location Data Limited:** Only country-level location exists (destination_country). Agent location and transaction location are missing.

3. **No Wallet-Agent Mapping:** No mechanism exists to track which wallets use which agents.

4. **Data Leakage Fields:** Several fields in transactions table could leak labels if used as ML inputs.

**Assessment:** The design is complete for Structuring and Network dimensions but INCOMPLETE for Agent dimension. The proposed schema changes (Section 17) address the identified weaknesses.

---

## 26. Critical Research Methodology Boundary

**Statement:** Database readiness is not model validation.

**Assessment:** This audit confirms that the database design (with proposed changes) will allow proper ML validation later, but does not guarantee model performance.

**Required for Later AI Validation:**
- Proper temporal separation (schema supports this)
- Wallet/customer isolation (schema supports this)
- Agent isolation (proposed schema supports this)
- Independent test data (schema supports this)
- Independent ground truth (schema supports this)
- Frozen model and threshold before final evaluation (implementation requirement)
- AML-specific metrics (implementation requirement)

**Status:** The database design will allow these requirements to be met. Actual model validation must be performed in a later AI phase.

---

## 27. Summary

### Current System Status

**Strengths:**
- Robust transaction data model with sufficient fields for structuring and network analysis
- Temporal safety supported by timestamp fields
- Alert and reporting tables are well-designed
- No data leakage inherent in schema design (leakage fields identified and documented)

**Weaknesses:**
- NO agent representation (critical gap for Agent AML dimension)
- Limited location data (only country-level)
- No wallet-agent mapping mechanism
- Some fields in transactions table could leak labels if used incorrectly

### Proposed Future Data Model

**Required Changes:**
1. Add `agents` table (CRITICAL)
2. Add `agent_id` field to `transactions` table (CRITICAL)
3. Add `wallet_agent_relationships` table (HIGH)
4. Add agent location fields to agents table (HIGH)
5. Add dimension-specific score fields to alerts table (MEDIUM)

**Optional Changes:**
1. Add `location` field to transactions table (MEDIUM)
2. Rename `account_number` to `wallet_number` (LOW - not recommended)

### Implementation Readiness

**Structuring Dimension:** ✅ READY - No schema changes required
**Network Dimension:** ✅ READY - No schema changes required
**Agent Dimension:** ❌ NOT READY - Requires critical schema changes

### Next Steps

**Stage 6:** Implement agent data model and agent behaviour detection
- Create agents table
- Add agent_id to transactions table
- Create wallet_agent_relationships table
- Implement agent-specific analytics
- Add agent score fields to alerts table

**STAGE 5 COMPLETE — WAITING FOR APPROVAL**
