"""Offline one-time guard tests; never connect to MySQL."""
from copy import deepcopy
import hashlib
import json

import pytest

from ml_v4.stage5c import refresh_test_attestation as repair
from ml_v4.stage5c import live_primary


def reviewed():
    return {
        'status': 'UNRESOLVED', 'fingerprint': repair.REVIEW_FINGERPRINT,
        'baseline': {
            'identity': {'database': 'v4_stage4s_disposable',
                         'server_uuid': repair.SERVER_UUID,
                         'principal': 'v4_stage4t_runner@127.0.0.1'},
            'counts': {'transactions': 8, 'canonical_mobile_money_events': 8,
                       'cmm_source_changes': 16, 'v4_shadow_results': 8,
                       'alerts': 1, 'sar_reports': 0, 'ctr_reports': 0},
            'history_assessment': {'freshness': 'UNKNOWN',
                                   'current_status': 'COMPLETE_VERIFIED',
                                   'current_issues': [],
                                   'current_canonical_event_ids': list(range(1, 9)),
                                   'current_source_revision': repair.CURRENT_REVISION,
                                   'attested_source_revision': repair.ATTESTED_REVISION,
                                   'attestation_sequence': 8, 'scope_revision': 1}},
        'prior_runs': [{'transactions': [{
            'transaction_id': 8, 'ai_risk_level': 'inference_error',
            'shadow_status': 'inference_error', 'prediction': None,
            'canonical_rows': 1,
            'capture_operations': ['SOURCE_INSERT', 'CANONICAL_INSERT']}]}],
    }


def test_review_accepts_only_pinned_issue_free_eight_event_state():
    repair.guard_review(reviewed())
    for mutate in (
        lambda x: x.update(fingerprint='changed'),
        lambda x: x['baseline']['counts'].update(cmm_source_changes=15),
        lambda x: x['baseline']['history_assessment'].update(current_issues=[{'code': 'GAP'}]),
        lambda x: x['baseline']['history_assessment'].update(current_source_revision='changed'),
        lambda x: x['prior_runs'][0]['transactions'][0].update(shadow_status='success'),
    ):
        candidate = deepcopy(reviewed())
        mutate(candidate)
        with pytest.raises(RuntimeError):
            repair.guard_review(candidate)


def test_current_guard_rejects_count_drift_and_source_change(monkeypatch):
    scope = {'revision': 1}
    current = {'status': 'COMPLETE_VERIFIED', 'issues': [],
               'canonical_event_ids': list(range(1, 9)),
               'source_revision': repair.CURRENT_REVISION,
               'boundary_digest': 'same'}
    previous = {'source_revision': repair.ATTESTED_REVISION,
                'sequence': 8, 'status': 'COMPLETE_VERIFIED',
                'scope_revision': 1, 'boundary_digest': 'same'}
    monkeypatch.setattr(repair.v1, 'identity', lambda *_args: {
        'principal': 'v4_stage4t_runner@127.0.0.1'})
    monkeypatch.setattr(repair.v1, '_triggers', lambda *_args: None)
    monkeypatch.setattr(repair.v1, '_boundary', lambda *_args: None)
    monkeypatch.setattr(repair, 'assess', lambda *_args: (scope, current, previous))
    monkeypatch.setattr(repair, 'validate_test', lambda *_args: {'status': 'inference_error'})

    class Cursor:
        def __init__(self, rows):
            self.rows = rows
        def fetchone(self):
            return self.rows[0] if self.rows else None
        def fetchall(self):
            return self.rows

    class Connection:
        counts = dict(reviewed()['baseline']['counts'], cmm_history_attestations=8)
        def execute(self, sql, params=()):
            if sql.startswith('SELECT COUNT(*) AS n FROM '):
                return Cursor([{'n': self.counts[sql.split('FROM ', 1)[1]]}])
            if 'ai_risk_level,risk_level FROM transactions WHERE id=8' in sql:
                return Cursor([{'ai_risk_level': 'inference_error',
                                'risk_level': 'pending_review'}])
            if 'body FROM v4_shadow_results WHERE transaction_id=8' in sql:
                return Cursor([{'body': json.dumps({'status': 'inference_error'})}])
            if 'operation FROM cmm_source_changes' in sql:
                return Cursor([{'operation': 'SOURCE_INSERT'},
                               {'operation': 'CANONICAL_INSERT'}])
            raise AssertionError(sql)

    connection = Connection()
    authority = {'principal': 'v4_stage4t_runner@127.0.0.1'}
    assert repair.guard_current(connection, authority)['current']['source_revision'] == repair.CURRENT_REVISION
    connection.counts = dict(connection.counts, cmm_source_changes=17)
    with pytest.raises(RuntimeError, match='counts changed'):
        repair.guard_current(connection, authority)
    connection.counts['cmm_source_changes'] = 16
    current['source_revision'] = 'unexpected'
    with pytest.raises(RuntimeError, match='differs'):
        repair.guard_current(connection, authority)


def test_no_environment_binding_means_no_attestation(monkeypatch):
    monkeypatch.delenv('STAGE5C_ATTEST_EXECUTE', raising=False)
    monkeypatch.setattr(repair, 'attest', lambda *_args: pytest.fail('Attestation attempted'))
    with pytest.raises(RuntimeError, match='environment not pinned'):
        repair.run()


def test_attestation_review_uses_dedicated_binding_before_database_access(monkeypatch):
    monkeypatch.setenv('STAGE5C_ATTEST_EXECUTE', 'YES')
    monkeypatch.setenv('V4_STAGE4T_EXPECTED_SERVER_UUID', repair.SERVER_UUID)
    monkeypatch.delenv('STAGE5C_EXECUTE', raising=False)
    monkeypatch.delenv('AML_PRIMARY_MODEL', raising=False)
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('MYSQL_URL', raising=False)
    monkeypatch.delenv('V4_SHADOW_ENABLED', raising=False)
    monkeypatch.setenv('V4_STAGE4T_TEST_DB_URL',
                       'mysql://v4_stage4t_runner:dummy@127.0.0.1:3306/v4_stage4s_disposable')
    monkeypatch.setattr(live_primary.v1, 'load_authority',
                        lambda: {'server_uuid': repair.SERVER_UUID})
    monkeypatch.setattr(live_primary.v1, 'connection',
                        lambda *_: pytest.fail('Reached verified database connection'))
    with pytest.raises(pytest.fail.Exception, match='Reached verified database connection'):
        live_primary.preflight(allow_stale=True, attestation_review=True)
    with pytest.raises(RuntimeError, match='Isolated execution environment not pinned'):
        live_primary.preflight(allow_stale=True)
    monkeypatch.setenv('AML_PRIMARY_MODEL', 'V4')
    with pytest.raises(RuntimeError, match='Isolated execution environment not pinned'):
        live_primary.preflight(allow_stale=True, attestation_review=True)
    monkeypatch.delenv('AML_PRIMARY_MODEL')
    monkeypatch.setenv('V4_STAGE4T_EXPECTED_SERVER_UUID', 'wrong')
    with pytest.raises(RuntimeError, match='Isolated execution environment not pinned'):
        live_primary.preflight(allow_stale=True, attestation_review=True)


def test_refresh_invokes_read_only_reconciliation_with_attestation_binding(tmp_path, monkeypatch):
    monkeypatch.setenv('STAGE5C_ATTEST_EXECUTE', 'YES')
    monkeypatch.setenv('V4_STAGE4T_EXPECTED_SERVER_UUID', repair.SERVER_UUID)
    for name in ('DATABASE_URL', 'MYSQL_URL', 'AML_PRIMARY_MODEL', 'V4_SHADOW_ENABLED'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('V4_STAGE4T_TEST_DB_URL',
                       'mysql://v4_stage4t_runner:dummy@127.0.0.1:3306/v4_stage4s_disposable')
    review = tmp_path / 'review.json'
    review.write_text(json.dumps(reviewed()), encoding='utf-8')
    monkeypatch.setattr(repair, 'REVIEW', review)
    monkeypatch.setattr(repair, 'OUT', tmp_path / 'out.json')
    monkeypatch.setattr(repair, 'MODEL_SHA', hashlib.sha256(repair.MODEL.read_bytes()).hexdigest())
    monkeypatch.setattr(repair, 'attest', lambda *_: pytest.fail('Attestation attempted'))
    def inspect(*, attestation_review=False):
        assert attestation_review is True
        raise RuntimeError('Read-only inspection reached')
    monkeypatch.setattr(repair, 'inspect_prior', inspect)
    with pytest.raises(RuntimeError, match='Read-only inspection reached'):
        repair.run()
