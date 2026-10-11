"""V4 primary rule policy must be explicit before a financial commit."""
import ast
from pathlib import Path

import pytest


def policy_functions():
    source = (Path(__file__).resolve().parents[1] / 'server.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and
                node.name in ('require_v4_rule_policy', 'set_rule_engine_enabled')]
    namespace = {'_RULE_ENGINE_POLICY': None, '_RULE_ENGINE_ENABLED': False,
                 'RuntimeError': RuntimeError}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<rule-policy>', 'exec'), namespace)
    return namespace, source


def test_v4_requires_explicit_rule_policy():
    namespace, source = policy_functions()
    with pytest.raises(RuntimeError, match='Explicit AML_RULE_ENGINE_ENABLED'):
        namespace['require_v4_rule_policy']()
    namespace['set_rule_engine_enabled'](True)
    namespace['require_v4_rule_policy']()
    assert namespace['_RULE_ENGINE_POLICY'] == 'ON'
    namespace['set_rule_engine_enabled'](False)
    namespace['require_v4_rule_policy']()
    assert namespace['_RULE_ENGINE_POLICY'] == 'OFF'
    namespace['_RULE_ENGINE_ENABLED'] = True
    with pytest.raises(RuntimeError, match='mismatch'):
        namespace['require_v4_rule_policy']()
    assert 'require_v4_rule_policy()' in source[source.index('def _prepare_v4_primary'):]
