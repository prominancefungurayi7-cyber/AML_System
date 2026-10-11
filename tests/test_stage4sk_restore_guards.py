"""Offline checks for pinned dump retargeting and restricted recovery grants."""
import pytest

from ml_v4.stage4sg.mysql_migration import EXPECTED_COUNTS
from ml_v4.stage4sg.recovery_guard import grant_check, REQUIRED
from ml_v4.stage4sg.restore_sql import prepare, RECOVERY
from ml_v4.stage4sg.verify_backup import TRIGGERS


def dump():
    lines = [
        'CREATE DATABASE /*!32312 IF NOT EXISTS*/ `v4_stage4s_disposable` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;\n',
        'USE `v4_stage4s_disposable`;\n',
    ]
    for table, count in EXPECTED_COUNTS.items():
        lines.append(f'CREATE TABLE `{table}` (\n')
        lines.append('  `id` bigint NOT NULL,\n')
        lines.append('  PRIMARY KEY (`id`)\n')
        lines.append(') ENGINE=InnoDB;\n')
        lines.extend(f'INSERT INTO `{table}` VALUES ({n});\n' for n in range(count))
    lines.extend(f'/*!50003 TRIGGER `{name}` AFTER INSERT ON `transactions` */\n'
                 for name in sorted(TRIGGERS))
    return ''.join(lines)


def test_retarget_pinned_dump_without_execution(tmp_path):
    source = tmp_path / 'v4_stage4s_disposable-20261009-225015-3681550.sql'
    target = tmp_path / 'recovery.sql'
    source.write_text(dump(), encoding='utf-8')
    import hashlib
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    result = prepare(source, target, sha)
    assert result['executed'] is False
    assert result['database'] == RECOVERY
    assert result['create_database_removed'] == 1
    assert 'CREATE DATABASE' not in target.read_text()
    assert 'USE `v4_stage4s_disposable`' not in target.read_text()
    assert f'USE `{RECOVERY}`' in target.read_text()


@pytest.mark.parametrize('extra', [
    'DROP DATABASE `aml`;\n',
    'USE `aml`;\n',
    'CREATE USER `other`@`localhost`;\n',
    'SELECT * FROM `v4_stage4s_disposable`.`transactions`;\n',
])
def test_retarget_rejects_unsafe_sql(tmp_path, extra):
    source = tmp_path / 'v4_stage4s_disposable-20261009-225015-3681550.sql'
    source.write_text(dump() + extra, encoding='utf-8')
    import hashlib
    with pytest.raises(ValueError):
        prepare(source, tmp_path / 'recovery.sql', hashlib.sha256(source.read_bytes()).hexdigest())


def test_recovery_grants_must_be_scoped_and_sufficient():
    valid = ["GRANT USAGE ON *.* TO `v4_stage4sk_restore`@`127.0.0.1`",
             'GRANT ' + ', '.join(sorted(REQUIRED)) +
             ' ON `v4_stage4sk_recovery`.* TO `v4_stage4sk_restore`@`127.0.0.1`']
    grant_check(valid)
    with pytest.raises(ValueError):
        grant_check(valid + ['GRANT SELECT ON aml.* TO x'])
    with pytest.raises(ValueError):
        grant_check(valid[:1])
