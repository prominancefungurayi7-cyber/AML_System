"""Offline contract checks; no schema migration or network connection."""
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

from werkzeug.datastructures import MultiDict
import pytest

from transaction_idempotency import is_unique_conflict, request_id


ROOT = Path(__file__).resolve().parents[1]


def test_uuidv4_request_id_must_be_single_and_canonical():
    valid = '123e4567-e89b-42d3-a456-426614174000'
    assert request_id(MultiDict([('client_request_id', valid)])) == valid
    for fields in ([], [('client_request_id', valid), ('client_request_id', valid)],
                   [('client_request_id', valid.upper())],
                   [('client_request_id', '123e4567-e89b-12d3-a456-426614174000')]):
        with pytest.raises(ValueError):
            request_id(MultiDict(fields))


def test_only_named_mysql_unique_index_is_a_retry():
    class Error:
        def __init__(self, name):
            self.errno = 1062
            self.name = name
        def __str__(self):
            return f"Duplicate entry for key '{self.name}'"
    assert is_unique_conflict(Error('uq_transactions_sender_request'))
    assert not is_unique_conflict(Error('PRIMARY'))
    assert not is_unique_conflict(SimpleNamespace(errno=1205))


def test_mysql_migration_requires_explicit_apply_before_database_access():
    command = [sys.executable, '-B', '-m', 'ml_v4.stage4sg.mysql_migration',
               '--expected-transactions', '4']
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode != 0
    assert 'Explicit --apply' in result.stderr
