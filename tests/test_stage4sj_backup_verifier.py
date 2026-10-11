"""Offline structural coverage checks for a disposable SQL backup."""
import pytest

from ml_v4.stage4sg.mysql_migration import EXPECTED_COUNTS
from ml_v4.stage4sg.verify_backup import TRIGGERS, verify


def sample():
    lines = ['USE `v4_stage4s_disposable`;\n']
    for table, count in EXPECTED_COUNTS.items():
        lines.append(f'CREATE TABLE `{table}` (`id` bigint);\n')
        lines.extend(f'INSERT INTO `{table}` VALUES ({n});\n' for n in range(count))
    lines.extend(f'/*!50003 TRIGGER `{name}` AFTER INSERT ON `transactions` */\n'
                 for name in sorted(TRIGGERS))
    return ''.join(lines)


def test_valid_structural_dump(tmp_path):
    path = tmp_path / 'backup.sql'
    path.write_text(sample(), encoding='utf-8')
    result = verify(path)
    assert result['status'] == 'STRUCTURALLY_VERIFIED'
    assert result['reviewed_row_counts'] == EXPECTED_COUNTS
    assert result['restore_tested'] is False


def test_reviewed_transaction_index_must_appear(tmp_path):
    path = tmp_path / 'backup.sql'
    path.write_text(sample(), encoding='utf-8')
    with pytest.raises(ValueError, match='index missing'):
        verify(path, ['idx_transactions_sender'])


@pytest.mark.parametrize('change', [
    lambda s: s.replace('USE `v4_stage4s_disposable`;', 'USE `aml`;'),
    lambda s: s.replace('INSERT INTO `transactions` VALUES (0);\n', ''),
    lambda s: s.replace('TRIGGER `cmm_tx_insert`', 'TRIGGER `other`'),
])
def test_rejects_wrong_database_missing_row_or_trigger(tmp_path, change):
    path = tmp_path / 'backup.sql'
    path.write_text(change(sample()), encoding='utf-8')
    with pytest.raises(ValueError):
        verify(path)
