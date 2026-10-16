"""Offline gates for the unactivated V4 primary route wiring."""
import ast
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREE = ast.parse((ROOT / 'server.py').read_text(encoding='utf-8'))


def _function(name, namespace):
    node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == name)
    node.decorator_list = []
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'server.py', 'exec'), namespace)
    return namespace[name]


def test_primary_mode_requires_explicit_setting(monkeypatch):
    enabled = _function('v4_primary_enabled', {'os': os})
    monkeypatch.delenv('AML_PRIMARY_MODEL', raising=False)
    assert enabled() is False
    monkeypatch.setenv('AML_PRIMARY_MODEL', 'V4')
    assert enabled() is True


def test_all_legacy_batch_routes_stop_before_any_database_work():
    for name in ('generate_structuring_scenario',
                 'generate_network_scenario', 'generate_agent_scenario'):
        route = _function(name, {'v4_primary_enabled': lambda: True})
        message, status = route()
        assert status == 503 and 'canonical' in message


def test_generation_dispatches_to_canonical_v4_before_legacy_database_work():
    route = _function('generate_transactions', {
        'v4_primary_enabled': lambda: True,
        'generate_v4_transactions': lambda: 'canonical V4 generator',
    })
    assert route() == 'canonical V4 generator'


def test_primary_branch_precedes_stage14_inference():
    node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef)
                and n.name == 'process_transaction_event')
    source = ast.get_source_segment((ROOT / 'server.py').read_text(encoding='utf-8'), node)
    assert source.index('if v4_primary_enabled():') < source.index('stage14_service.predict')
    assert 'if emit_events:' in source[source.index('if v4_primary_enabled():'):
                                       source.index('stage14_service.predict')]


def test_customer_commits_before_primary_completion_and_notification():
    node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef)
                and n.name == 'create_transaction')
    source = ast.get_source_segment((ROOT / 'server.py').read_text(encoding='utf-8'), node)
    assert source.index('get_db().commit()') < source.index('v4_primary.complete_committed(')
    assert source.index('v4_primary.complete_committed(') < source.index(
        'broadcast_committed_customer_transaction(get_db(), transaction_id, created_alert)')
    assert 'canonical_event is None' in source
