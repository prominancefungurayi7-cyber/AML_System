"""Generate disposable schema SQL from current application DDL without startup/DB access."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from database import get_schema_sql

database_source = ROOT / 'database.py'
server_source = ROOT / 'server.py'
sql = get_schema_sql('mysql://v4_stage4t_runner@localhost/v4_stage4s_disposable')
parts = [p.strip() for p in sql.split(';') if p.strip()]
tables = {}
for part in parts:
    match = re.match(r'CREATE TABLE IF NOT EXISTS (\w+)\s*\(', part, re.I)
    if not match:
        raise AssertionError('Unexpected application DDL statement')
    name = match.group(1)
    if name in tables:
        raise AssertionError('Duplicate table')
    tables[name] = part.replace('CREATE TABLE IF NOT EXISTS', 'CREATE TABLE', 1)

assert {'users', 'agents', 'transactions', 'alerts', 'behavioral_profiles',
        'sar_reports', 'ctr_reports', 'system_activity_log', 'activity_log',
        'watchlist'} == set(tables)

# MySQL requires the agents parent before transactions. The frozen Event
# contract requires preserving the UTC six-digit string supplied by the route.
transactions = tables['transactions']
transactions, count = re.subn(r'\btimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP\b',
                               'timestamp VARCHAR(40) NOT NULL', transactions, count=1)
assert count == 1
tables['transactions'] = transactions
alerts = tables['alerts']
alerts, count = re.subn(r'\btimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP\b',
                        'timestamp VARCHAR(40) NOT NULL', alerts, count=1)
assert count == 1
tables['alerts'] = alerts

tree = ast.parse(server_source.read_text(encoding='utf-8-sig'))
migrate = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_migrate_mysql')
assignment = next(n for n in migrate.body if isinstance(n, ast.Assign) and any(
    isinstance(target, ast.Name) and target.id == 'column_migrations' for target in n.targets))
columns = ast.literal_eval(assignment.value)

order = ['users', 'agents', 'transactions', 'alerts', 'behavioral_profiles',
         'sar_reports', 'ctr_reports', 'system_activity_log', 'activity_log', 'watchlist']
out = ['-- Stage4U disposable MySQL application schema. No data or credentials.',
       '-- Generated from database.py and server.py static migration literals.',
       '-- Apply only after verifying DATABASE() = v4_stage4s_disposable and restricted grants.',
       '']
for name in order:
    out.append(tables[name] + ';')
    out.append('')

alterations = []
for table, definitions in columns.items():
    if table not in tables:
        raise AssertionError('Unknown migration table')
    base = tables[table]
    for column, definition in definitions:
        if re.search(r'(?m)^\s*' + re.escape(column) + r'\s+', base):
            continue
        if not re.fullmatch(r'[a-z_]+', table) or not re.fullmatch(r'[a-z_]+', column):
            raise AssertionError('Invalid static migration name')
        # MySQL 8 does not accept a literal default on LONGTEXT. The route
        # supplies this JSON column explicitly; omit only that SQL default.
        if column == 'rules_triggered' and definition == "LONGTEXT DEFAULT '[]'":
            definition = 'LONGTEXT'
        alterations.append(f'ALTER TABLE {table} ADD COLUMN {column} {definition};')
out.extend(alterations)
out.append('')

indexes = [
    ('idx_stage4u_tx_sender_time', 'transactions', 'sender_account,timestamp,id'),
    ('idx_stage4u_tx_receiver_time', 'transactions', 'receiver_account,timestamp,id'),
    ('idx_stage4u_tx_agent_time', 'transactions', 'agent_id,timestamp,id'),
    ('idx_stage4u_alert_account', 'alerts', 'account_number,status,id'),
    ('idx_stage4u_activity_actor', 'activity_log', 'actor,timestamp,id'),
    ('idx_stage4u_watchlist_account', 'watchlist', 'account_number'),
]
out.extend(f'CREATE INDEX {name} ON {table} ({fields});' for name, table, fields in indexes)
out.append('')
rendered = '\n'.join(out)
assert 'INSERT INTO' not in rendered.upper() and 'DROP ' not in rendered.upper()
assert 'CREATE DATABASE' not in rendered.upper() and 'CREATE USER' not in rendered.upper()
assert 'timestamp VARCHAR(40) NOT NULL' in tables['transactions']
(OUT / 'application_schema_only.sql').write_text(rendered, encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

review = {
    'status': 'GENERATED_NOT_APPLIED',
    'source_hashes': {'database.py': sha(database_source), 'server.py': sha(server_source)},
    'ordered_tables': order,
    'migration_additions': alterations,
    'indexes': indexes,
    'timestamp_treatment': 'Transaction and alert event timestamps preserve six-digit UTC text in VARCHAR(40).',
    'financial_rows_copied': 0,
    'schema_sha256': sha(OUT / 'application_schema_only.sql'),
    'limits': 'Static SQL review only; server syntax, grants and Flask route compatibility require isolated MySQL verification.'
}
(OUT / 'schema_review.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
print('Generated schema-only SQL:', len(order), 'tables,', len(alterations), 'migration additions,', len(indexes), 'indexes.')
