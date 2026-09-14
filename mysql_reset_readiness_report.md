# MySQL Reset Permission and Execution Readiness Report

**Date:** September 14, 2026  
**Purpose:** Read-only audit of MySQL environment for database reset readiness  
**Type:** READ-ONLY AUDIT (NO CHANGES MADE)

---

## 1. Environment

| Item | Value |
|------|-------|
| OS | Windows 11 (10.0.26200) |
| MySQL Version | 8.0.46 |
| Host | 127.0.0.1 |
| Port | 3306 |
| Database | aml |
| Application MySQL User | aml |
| Database Type | MySQL |

**Configuration source**

- Application reads `DATABASE_URL` first, then `MYSQL_URL`, then the default in `config.py`.
- `DATABASE_URL` is set in the environment (via `.env`).
- `MYSQL_URL` is not set.
- Default fallback in `config.py`: `mysql://aml@127.0.0.1:3306/aml` (password loaded from env/URL only; not reported here).

**Safe connection summary**

```text
Host: 127.0.0.1
Port: 3306
Database: aml
User: aml
Database type: MySQL
Connection: PASS
```

---

## 2. Connection

**MySQL connection:** PASS

- Connection to MySQL server succeeded.
- Connection to the `aml` database succeeded.
- Engine confirmed as MySQL 8.0.46 (not SQLite or PostgreSQL).
- Database character set: `utf8mb4`
- Database collation: `utf8mb4_unicode_ci`

---

## 3. Current Database Verification

### Database state

| Check | Result |
|-------|--------|
| Database exists | YES |
| Connection succeeds | YES |
| Schema readable | YES |
| Tables accessible | YES |
| Foreign keys inspectable | YES |
| Indexes inspectable | YES |
| Engine is MySQL | YES |

### Current table verification

All 15 audited tables exist:

- users
- transactions
- agents
- alerts
- sar_reports
- ctr_reports
- customer_baselines
- conversations
- messages
- unread_messages
- user_presence
- behavioral_profiles
- system_activity_log
- activity_log
- watchlist

### Current row counts

| Table | Row Count |
|-------|-----------|
| users | 17 |
| transactions | 7,028 |
| agents | 0 |
| alerts | 2,201 |
| sar_reports | 0 |
| ctr_reports | 149 |
| customer_baselines | 0 |
| conversations | 2 |
| messages | 10 |
| unread_messages | 2 |
| user_presence | 4 |
| behavioral_profiles | 15 |
| system_activity_log | 0 |
| activity_log | 67 |
| watchlist | 4 |

**Total records:** 9,599 across 15 tables.

**Note:** No data was modified during this audit. All counts were obtained with read-only `SELECT COUNT(*)` queries.

### Current live schema notes

- The live database matches the production Flask path more closely than the legacy `database.py` DDL helper.
- Live `transactions` columns include AI/rule/reporting fields used by `server.py` (`generated_label`, `destination_country`, `agent_id`, etc.).
- Live database currently enforces fewer foreign keys than `clean_aml_mysql_schema.sql` would create. Existing FKs are mainly on messaging tables and `transactions.agent_id`.

---

## 4. MySQL Privileges

### Current user grants

```text
GRANT USAGE ON *.* TO `aml`@`127.0.0.1`
GRANT ALL PRIVILEGES ON `aml`.* TO `aml`@`127.0.0.1`
```

### Privilege analysis

| Privilege | Available | Required for Full Reset |
|-----------|-----------|-------------------------|
| CREATE DATABASE | NO | YES |
| DROP DATABASE | NO | YES |
| CREATE TABLE | YES | YES |
| ALTER TABLE | YES | YES |
| CREATE INDEX | YES | YES |
| Foreign Keys | YES | YES |
| SELECT | YES | YES |
| INSERT | YES | YES |
| UPDATE | YES | YES |
| DELETE | YES | YES |

**Interpretation**

- Global privileges for `aml@127.0.0.1`: `USAGE` only.
- Schema privileges on `aml.*`: full table-level privileges (`CREATE`, `DROP`, `ALTER`, `INDEX`, `REFERENCES`, `INSERT`, `UPDATE`, `DELETE`, etc.).
- `ALL PRIVILEGES ON aml.*` applies to objects inside the database. It does **not** grant global `CREATE DATABASE` or `DROP DATABASE`.

```text
FULL DATABASE RESET PERMISSION: NOT AVAILABLE
```

**Missing privileges for the script as written**

- Global `DROP` required for `DROP DATABASE aml;`
- Global `CREATE` required for `CREATE DATABASE aml;`

The application account can rebuild tables inside the existing `aml` database, but it cannot execute the opening database-level statements in `clean_aml_mysql_schema.sql` without a MySQL administrator account.

---

## 5. Schema Validation

Audit target: `clean_aml_mysql_schema.sql`  
Validation method: static inspection only. Destructive statements were **not** executed.

### Database section

| Check | Result |
|-------|--------|
| `DROP DATABASE IF EXISTS aml` syntax | Valid MySQL |
| `CREATE DATABASE aml CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci` | Valid MySQL |
| `USE aml` | Correct |
| Character set | Appropriate (`utf8mb4`) |
| Collation | Appropriate (`utf8mb4_unicode_ci`) |

### Table creation order

**Result:** PASS

Dependency order is valid:

```text
users
agents
    ↓
customer_baselines
behavioral_profiles
    ↓
transactions
    ↓
alerts
sar_reports
ctr_reports
    ↓
conversations
    ↓
messages
unread_messages
user_presence
system_activity_log
activity_log
watchlist
```

All referenced parent tables are created before child tables.

### Foreign keys

**Result:** PASS with minor type-consistency warnings

Verified key relationships:

| From Table | From Column | To Table | To Column | Status |
|------------|-------------|----------|-----------|--------|
| transactions | sender_account | users | account_number | Valid |
| transactions | receiver_account | users | account_number | Valid |
| transactions | agent_id | agents | id | Valid |
| alerts | transaction_id | transactions | id | Valid syntax; INT vs BIGINT mismatch |
| sar_reports | alert_id | alerts | id | Valid syntax; INT vs BIGINT mismatch |
| ctr_reports | transaction_id | transactions | id | Valid syntax; INT vs BIGINT mismatch |
| behavioral_profiles | account_number | users | account_number | Valid |
| customer_baselines | account_number | users | account_number | Valid |
| conversations | participant_1 / participant_2 | users | username | Valid |
| messages | conversation_id / sender_username / receiver_username | conversations / users | id / username | Valid |
| unread_messages | user_username / conversation_id | users / conversations | username / id | Valid |
| user_presence | username / typing_in_conversation | users / conversations | username / id | Valid |

**Warnings**

- `alerts.transaction_id`, `sar_reports.alert_id`, and `ctr_reports.transaction_id` are declared as `INT` while parent primary keys are `BIGINT`. MySQL will usually accept this, but `BIGINT` throughout would be safer for large datasets.

**Application alignment**

- Production `server.py` SAR flow uses `sar_reports.alert_id`, which matches the clean schema.
- Production CTR flow uses `ctr_reports.transaction_id`, which matches the clean schema.
- Legacy helper functions in `reports.py` still reference an older SAR shape (`transaction_id`, `filing_reason`). That legacy module is not the primary production path used by `server.py`.

### Indexes

**Result:** PASS with minor gaps

Present in `clean_aml_mysql_schema.sql` and required by the application:

- Transaction indexes: sender, receiver, timestamp, risk_level, agent
- Agent indexes: region, city
- Alert indexes: transaction_id, account_number, status, timestamp, risk_level
- SAR/CTR indexes: alert_id, transaction_id
- Messaging indexes: conversation_id, sender_username, receiver_username, unread/user presence keys

**Missing compared with `database.py` helper DDL**

These indexes are defined in `database.py` for SQLite/Postgres paths but are **not** present in `clean_aml_mysql_schema.sql`:

- `idx_activity_user` on `system_activity_log(user_id)`
- `idx_activity_log_actor` on `activity_log(actor)`
- `idx_watchlist_type` on `watchlist(list_type)`
- `idx_watchlist_id_number` on `watchlist(id_number)`

These are performance indexes, not hard blockers for application startup.

### Constraints

**Result:** PASS

- Primary keys defined on all tables.
- Unique constraints preserved for usernames, emails, account numbers, agent codes, conversation pairs.
- Required `NOT NULL` fields align with current Flask inserts.
- `AUTO_INCREMENT` used on surrogate keys.
- Defaults preserved for status/risk/KYC fields.
- Foreign keys use valid MySQL syntax.

### Monetary and numeric data types

**Result:** PASS

- Monetary/numeric fields use `DOUBLE` (`balance`, `amount`, `risk_score`, `rule_score`, `ai_confidence`, baseline statistics).
- This matches current application code and the live MySQL schema.
- Python code treats these as floating-point values throughout transaction processing and dashboards.

### Application compatibility

| Area | Status | Notes |
|------|--------|-------|
| Flask startup | Compatible | All required tables are defined |
| Authentication | Compatible | `users` structure matches login/registration flows |
| Users/wallets | Compatible | `account_number` remains wallet identifier |
| Transactions | Compatible | Includes AI, rule, agent, and reporting fields used by `server.py` |
| Agents | Compatible | `agents` table matches agent-aware transaction path |
| Alerts | Compatible | Alert workflow fields match compliance UI |
| SAR/CTR | Compatible | Matches production `server.py` report flows |
| Conversations/messages | Compatible | Messaging schema matches `messaging.py` |
| Unread messages / presence | Compatible | Notification and Socket.IO support tables present |
| API functionality | Compatible | No missing core tables identified |
| Socket.IO | Compatible | No DB dependency gaps identified |

**Non-blocking legacy note:** `reports.py` contains older SAR/CTR insert shapes. Production routes in `server.py` use the newer alert-linked SAR schema defined in `clean_aml_mysql_schema.sql`.

---

## 6. Reset Readiness

```text
NOT READY FOR FULL DATABASE RESET
```

**Why**

The approved reset script begins with:

```sql
DROP DATABASE aml;
CREATE DATABASE aml;
```

The configured application account `aml@127.0.0.1` does **not** have global `DROP DATABASE` or `CREATE DATABASE` privileges. Running `clean_aml_mysql_schema.sql` unchanged with the application account will fail at the first database-level statement.

Everything else needed for a rebuild is available at the table level inside the existing `aml` database.

---

## 7. Required Action

Before the approved reset can proceed, choose one of the following:

### Option A — Recommended for the current script

Run `clean_aml_mysql_schema.sql` using a MySQL administrator account that has global `CREATE` and `DROP` privileges.

Required admin capability:

```sql
GRANT CREATE, DROP ON *.* TO '<admin-user>'@'<host>';
```

Or execute the script while connected as `root` or another existing admin account.

Do **not** attempt to bypass security controls or guess admin credentials.

### Option B — Safer alternative using the application account

```text
Option A: DROP DATABASE + CREATE DATABASE
Status: unavailable because global CREATE/DROP DATABASE permission is missing

Option B: DROP TABLE in dependency-safe order and recreate tables
Status: possible
```

The `aml` account **can** perform a table-level rebuild inside the existing `aml` database because it has `DROP`, `CREATE`, `ALTER`, `INDEX`, `REFERENCES`, and DML privileges on `aml.*`.

A table-level rebuild would require:

1. Omitting the opening `DROP DATABASE` / `CREATE DATABASE` statements.
2. Disabling foreign key checks temporarily or dropping tables in reverse dependency order.
3. Running the table/index creation portion of `clean_aml_mysql_schema.sql`.
4. Restarting the Flask app to seed admin/compliance accounts.

This audit did **not** execute Option B.

---

## 8. ML Protection Check

This audit made:

- no model changes
- no feature changes
- no label changes
- no dataset changes
- no training changes
- no threshold changes
- no test-set changes

No ML files were modified. The frozen 30-feature design remains unchanged. This stage only inspected database readiness for a future clean application database phase.

---

## 9. Credential Safety

This audit did **not**:

- print passwords
- expose `.env` secrets
- commit credentials
- create plaintext passwords
- change MySQL authentication
- change user permissions

Only safe configuration values were reported: host, port, database name, and username.

---

## 10. Data Loss Warning

If a reset is executed later, the current database contains **9,599 records**, including:

- 17 users
- 7,028 transactions
- 2,201 alerts
- 149 CTR reports
- 15 behavioral profiles
- messaging, activity, and watchlist data

This data will be destroyed unless a backup exists.

---

## 11. Post-Reset Steps (after explicit approval)

1. Execute the approved reset using either an admin account (Option A) or a table-level rebuild script (Option B).
2. Start the Flask application to seed default accounts and demo data.
3. Verify login, dashboards, transaction processing, alerts, SAR/CTR flows, messaging, and Socket.IO.

---

## Final Summary

| Area | Result |
|------|--------|
| Environment | Windows + MySQL 8.0.46 on 127.0.0.1:3306 |
| Connection | PASS |
| Current database verification | PASS (all 15 tables present) |
| Table-level privileges | PASS |
| Database-level reset privileges | FAIL |
| Schema validation | PASS with minor index/type warnings |
| Application compatibility | PASS for production `server.py` path |
| ML protection | PASS (zero ML impact) |

```text
FULL DATABASE RESET PERMISSION: NOT AVAILABLE
NOT READY FOR FULL DATABASE RESET
```

**No changes were made to the current `aml` database during this audit.**

**STOP — wait for explicit approval before performing the actual database reset.**
