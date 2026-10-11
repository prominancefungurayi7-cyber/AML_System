"""A failed test worker must not turn an unattested event into trusted history."""
import json

import pytest

from canonical_history import freshness
from ml_v4.stage5c import live_primary


def test_new_committed_event_without_worker_attestation_is_unknown(monkeypatch):
    scope = {'revision': 1}
    current = {'status': 'COMPLETE_VERIFIED', 'issues': [],
               'source_revision': 'new', 'boundary_digest': 'same',
               'canonical_event_ids': [5, 6, 7, 8],
               'observed_through_key': ['2026-10-09T22:00:00Z', 8]}
    prior = {'scope_revision': 1, 'source_revision': 'old',
             'boundary_digest': 'same', 'status': 'COMPLETE_VERIFIED',
             'attestation_id': 'prior', 'sequence': 7}
    assert freshness(scope, current, prior) == 'UNKNOWN'
    monkeypatch.setattr(live_primary, 'assess', lambda _db, _scope: (scope, current, prior))
    diagnosis = live_primary._history_diagnosis(object())
    assert diagnosis['freshness'] == 'UNKNOWN'
    assert diagnosis['current_status'] == 'COMPLETE_VERIFIED'
    assert diagnosis['current_issues'] == []
    assert diagnosis['current_canonical_event_ids'][-1] == 8
    assert diagnosis['attested_source_revision'] != diagnosis['current_source_revision']


def test_unresolved_read_only_review_is_saved_and_blocks_new_fixtures(tmp_path, monkeypatch):
    review = tmp_path / 'interrupted_review.json'
    monkeypatch.setattr(live_primary, 'REVIEW', review)
    monkeypatch.setattr(live_primary, 'inspect_prior', lambda: {
        'status': 'UNRESOLVED', 'baseline': {'history_assessment': {
            'freshness': 'UNKNOWN', 'current_issues': []}}})
    with pytest.raises(RuntimeError, match='no new fixture'):
        live_primary.save_review()
    assert json.loads(review.read_text(encoding='utf-8'))['status'] == 'UNRESOLVED'
