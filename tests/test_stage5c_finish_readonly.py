"""The Stage5C completion path cannot submit a payment."""
from pathlib import Path

import pytest

from ml_v4.stage5c import finish_readonly


def test_unreconciled_or_changed_counts_stop_before_flask(monkeypatch):
    monkeypatch.setattr(finish_readonly, 'load_test_application',
                        lambda: pytest.fail('Flask loaded for unresolved state'))
    monkeypatch.setattr(finish_readonly, 'inspect_prior', lambda: {
        'status': 'UNRESOLVED', 'baseline': {'history': 'UNKNOWN'}})
    with pytest.raises(RuntimeError, match='history or balances unresolved'):
        finish_readonly.run()
    monkeypatch.setattr(finish_readonly, 'inspect_prior', lambda: {
        'status': 'RECONCILED', 'baseline': {'history': 'COMPLETE_VERIFIED',
            'counts': {'transactions': 9, 'canonical_mobile_money_events': 8,
                       'cmm_source_changes': 16, 'v4_shadow_results': 8}}})
    with pytest.raises(RuntimeError, match='counts changed'):
        finish_readonly.run()


def test_read_only_runner_has_no_transaction_post():
    source = Path(finish_readonly.__file__).read_text(encoding='utf-8')
    assert "client.post(" not in source
    assert 'INSERT INTO' not in source and 'UPDATE ' not in source
    launcher = (Path(__file__).resolve().parents[1] /
                'ml_v4/stage5c/run_live_primary.ps1').read_text(encoding='utf-8')
    assert '[switch]$FinishReadOnly' in launcher
    assert '-m ml_v4.stage5c.finish_readonly' in launcher
