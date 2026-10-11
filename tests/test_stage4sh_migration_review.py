"""Offline checks for the disposable migration's existing-row guard."""
from copy import deepcopy

import pytest

from ml_v4.stage4sg.mysql_migration import EXPECTED_COUNTS, existing_records


class ReadOnlyRows:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql):
        assert sql.startswith('SELECT ')
        self.table = sql.split(' FROM ', 1)[1].split(' ', 1)[0]
        return self

    def fetchall(self):
        return self.rows[self.table]


def test_existing_row_guard_detects_changes_and_count_drift():
    rows = {name: [{'id': n} for n in range(count)]
            for name, count in EXPECTED_COUNTS.items()}
    original = existing_records(ReadOnlyRows(rows), ['id'])
    changed = deepcopy(rows)
    changed['transactions'][0]['id'] = 99
    assert existing_records(ReadOnlyRows(changed), ['id']) != original
    changed['transactions'].pop()
    with pytest.raises(RuntimeError, match='Existing disposable record count changed'):
        existing_records(ReadOnlyRows(changed), ['id'])
