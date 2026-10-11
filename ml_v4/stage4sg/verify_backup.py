"""Structural verification of a single-database mysqldump; never restores it."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from ml_v4.stage4sg.mysql_migration import EXPECTED_COUNTS
from ml_v4.test_binding.v1 import DATABASE

TRIGGERS = {f'cmm_{prefix}_{operation}' for prefix in ('tx', 'ce')
            for operation in ('insert', 'update', 'delete')}


def verify(path, expected_indexes=()):
    file = Path(path)
    if not file.is_file() or file.stat().st_size == 0:
        raise ValueError('Backup is missing or empty')
    digest = hashlib.sha256()
    tables = set()
    triggers = set()
    counts = dict.fromkeys(EXPECTED_COUNTS, 0)
    databases = set()
    transaction_ddl = []
    in_transactions = False
    with file.open('rb') as stream:
        for raw in stream:
            digest.update(raw)
            line = raw.decode('utf-8', errors='replace')
            databases.update(re.findall(r'^USE\s+`?([A-Za-z0-9_]+)`?\s*;', line, re.I))
            match = re.search(r'\bCREATE TABLE\s+`([^`]+)`', line, re.I)
            if match:
                tables.add(match.group(1))
                in_transactions = match.group(1) == 'transactions'
            if in_transactions:
                transaction_ddl.append(line)
                if re.match(r'^\)\s*(ENGINE=|;)', line, re.I):
                    in_transactions = False
            match = re.search(r'\bTRIGGER\s+`([^`]+)`', line, re.I)
            if match:
                triggers.add(match.group(1))
            match = re.match(r'^INSERT INTO\s+`([^`]+)`\s', line, re.I)
            if match and match.group(1) in counts:
                counts[match.group(1)] += 1
    if databases != {DATABASE}:
        raise ValueError('Dump database selection differs from disposable database')
    if not set(EXPECTED_COUNTS).issubset(tables):
        raise ValueError('Required table definition missing')
    if triggers != TRIGGERS:
        raise ValueError('Capture trigger definitions differ')
    if counts != EXPECTED_COUNTS:
        raise ValueError('Dump row coverage differs from reviewed preflight')
    ddl = ''.join(transaction_ddl)
    dump_indexes = set(re.findall(r'\b(?:UNIQUE\s+)?KEY\s+`([^`]+)`', ddl, re.I))
    if re.search(r'\bPRIMARY KEY\b', ddl, re.I):
        dump_indexes.add('PRIMARY')
    for index in expected_indexes:
        if index == 'PRIMARY':
            present = re.search(r'\bPRIMARY KEY\b', ddl, re.I)
        else:
            present = re.search(r'\b(?:UNIQUE\s+)?KEY\s+`' + re.escape(index) + r'`', ddl, re.I)
        if not present:
            raise ValueError('Reviewed transaction index missing from dump')
    result = {'status': 'STRUCTURALLY_VERIFIED', 'path': str(file.resolve()),
              'bytes': file.stat().st_size, 'sha256': digest.hexdigest(),
              'database': DATABASE, 'table_definitions': sorted(tables),
              'capture_triggers': sorted(triggers), 'reviewed_row_counts': counts,
              'reviewed_transaction_indexes': sorted(expected_indexes),
              'dump_transaction_indexes': sorted(dump_indexes),
              'restore_tested': False}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dump_path')
    parser.add_argument('--expected-index', action='append', default=[])
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.dump_path, args.expected_index), indent=2, sort_keys=True))
    except Exception as exc:
        print('Backup structural verification stopped: ' + type(exc).__name__)
        raise SystemExit(1)
