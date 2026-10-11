"""Explicit test-only schema installer; refuses all writes until identity/grants pass.

Do not run until administrator provisioning is complete. No application import.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from ml_v4.test_binding import v1

expected_uuid = os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID', '')
parsed = v1.config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
if not expected_uuid:
    raise v1.BindingError('Expected test server UUID required')

review = json.loads((OUT / 'schema_review.json').read_text(encoding='utf-8'))
schema = OUT / 'application_schema_only.sql'
if hashlib.sha256(schema.read_bytes()).hexdigest() != review['schema_sha256']:
    raise v1.BindingError('Schema review hash mismatch')

import mysql.connector
from database import DatabaseAdapter
from urllib.parse import unquote

connection = DatabaseAdapter(mysql.connector.connect(
    host=parsed.hostname, port=parsed.port or 3306,
    user=v1.USER, password=unquote(parsed.password), database=v1.DATABASE,
    connection_timeout=5, charset='utf8mb4'), 'mysql')
try:
    v1.identity(connection, expected_uuid)
    if connection.execute('SHOW TABLES').fetchall():
        raise v1.BindingError('Schema installer requires an empty disposable database')
    # DDL auto-commits on MySQL. An interruption needs administrator review;
    # this tool has no reset or resume mode.
    connection.executescript(schema.read_text(encoding='utf-8'))
    connection.commit()
    actual_tables = {next(iter(row.values())) for row in connection.execute('SHOW TABLES').fetchall()}
    if actual_tables != set(review['ordered_tables']):
        raise v1.BindingError('Installed application table set mismatch')
    columns = {row['Field']: row['Type'].lower() for row in
               connection.execute('SHOW COLUMNS FROM transactions').fetchall()}
    if (columns.get('id') != 'bigint' or columns.get('timestamp') != 'varchar(40)' or
        not {'sender_account', 'receiver_account', 'amount', 'transaction_type',
             'currency', 'agent_id', 'status', 'risk_score', 'rule_score'}.issubset(columns)):
        raise v1.BindingError('Installed transaction schema mismatch')
    indexes = {row['Key_name'] for row in connection.execute('SHOW INDEX FROM transactions').fetchall()}
    if not {'PRIMARY', 'idx_stage4u_tx_sender_time',
            'idx_stage4u_tx_receiver_time', 'idx_stage4u_tx_agent_time'}.issubset(indexes):
        raise v1.BindingError('Installed transaction indexes incomplete')
    if any(connection.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']
           for table in review['ordered_tables']):
        raise v1.BindingError('Schema installer unexpectedly found application rows')
    v1.identity(connection, expected_uuid)
    print('Disposable application schema installed; no financial rows inserted.')
finally:
    connection.close()
