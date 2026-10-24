"""Read-only explanation selection after an audited retry."""
import json
import pytest
from tools.v4_model_evidence import recorded_decision
from test_stage5a_v4_primary import success
import v4_shadow


@pytest.mark.parametrize('retry_success', [False, True])
def test_evidence_uses_validated_successful_retry(monkeypatch, retry_success):
    original = v4_shadow.error(42, 'RESOURCE_ERROR')
    monkeypatch.setattr(v4_shadow, 'get', lambda *_: dict(original))
    class Connection:
        def execute(self, query, params):
            assert "event_kind='COMPLETED'" in query and "outcome='success'" in query
            assert params == (42,)
            return self
        def fetchone(self):
            return {'result_body': json.dumps(success(42, .8))} if retry_success else None
    if retry_success:
        assert recorded_decision(Connection(), 42)['suspicious_probability'] == .8
    else:
        with pytest.raises(ValueError, match='No successful recorded'):
            recorded_decision(Connection(), 42)
    assert original['status'] == 'inference_error'


def test_evidence_rejects_mismatched_retry(monkeypatch):
    monkeypatch.setattr(v4_shadow, 'get', lambda *_: v4_shadow.error(42, 'RESOURCE_ERROR'))
    class Connection:
        def execute(self, *_): return self
        def fetchone(self): return {'result_body': json.dumps(success(99, .8))}
    with pytest.raises(ValueError, match='Contract mismatch'):
        recorded_decision(Connection(), 42)
