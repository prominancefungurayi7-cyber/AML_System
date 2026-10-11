"""Regression checks for account/date CTR schema used by MySQL."""
import ast
from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'server.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)


def function(name, namespace):
    node = next(node for node in TREE.body if isinstance(node, ast.FunctionDef)
                and node.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'server.py', 'exec'), namespace)
    return namespace[name]


def test_committed_notification_does_not_query_ctr_by_transaction_id():
    events = []
    queries = []

    class Connection:
        def execute(self, sql, params=()):
            queries.append(sql)
            if 'ctr_reports' in sql:
                raise AssertionError('CTR has no transaction_id relationship')
            if 'FROM transactions' in sql:
                return type('Cursor', (), {'fetchone': lambda _self: {'id': 7,
                    'ctr_required': 1, 'ai_risk_level': 'normal'}})()
            if 'FROM alerts' in sql:
                return type('Cursor', (), {'fetchone': lambda _self: None})()
            raise AssertionError(sql)

    notify = function('broadcast_committed_customer_transaction', {
        '_transaction_payload': lambda row: dict(row),
        'broadcast_event': lambda kind, payload: events.append((kind, payload)),
        'broadcast_stats': lambda _conn: events.append(('stats', None)),
        'broadcast_report_event': lambda *_args: AssertionError('No linked CTR report'),
    })
    notify(Connection(), 7, None)
    assert [kind for kind, _ in events] == ['transaction', 'stats']
    assert events[0][1]['ctr_required'] == 1
    assert not any('ctr_reports' in query for query in queries)


def test_v4_precommit_sets_ctr_flag_without_inventing_report_link():
    queries = []
    params = []

    class Connection:
        engine = 'mysql'
        def execute(self, sql, values=()):
            queries.append(sql)
            params.append(values)
            if 'canonical_mobile_money_events' in sql:
                return type('Cursor', (), {'fetchone': lambda _self: {'transaction_id': 7}})()
            return None

    prepare = function('_prepare_v4_primary', {
        'CTR_THRESHOLD': 10000, 'json': json, 'datetime': datetime,
        'timezone': timezone,
        'create_alert_if_needed': lambda *_args, **_kwargs: None,
    })
    prepare(Connection(), 7, 'WALLET', 10000, 'deposit',
            '2026-10-09T00:00:00Z', 'ZW', 0, 'normal',
            'No rule indicators', '[]', [], [])
    update = next(values for sql, values in zip(queries, params)
                  if sql.startswith('UPDATE transactions'))
    assert update[10] == 1  # ctr_required parameter
    assert not any('ctr_reports' in sql for sql in queries)


def test_defined_ctr_schema_is_account_and_filing_based():
    source = (ROOT / 'database.py').read_text(encoding='utf-8')
    table = source.split('CREATE TABLE IF NOT EXISTS ctr_reports (', 1)[1].split(');', 1)[0]
    assert 'account_number' in table and 'total_amount' in table
    assert 'transaction_count' in table and 'filing_date' in table
    assert 'transaction_id' not in table
