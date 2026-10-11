"""Pin and retarget the Stage4S-J dump without executing SQL."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from ml_v4.stage4sg.verify_backup import verify

SOURCE = 'v4_stage4s_disposable'
RECOVERY = 'v4_stage4sk_recovery'
EXPECTED_SHA256 = 'b883ecb0fa7132106b5b1eeb91f26369e708e51ec54298b542251a9dd8e6c85c'
EXPECTED_NAME = 'v4_stage4s_disposable-20261009-225015-3681550.sql'

CREATE = re.compile(r'^(CREATE DATABASE\s+(?:/\*!\d{5} IF NOT EXISTS\*/\s+)?)(`' + SOURCE + r'`)(\s+.*;\s*)$', re.I)
USE = re.compile(r'^USE\s+`' + SOURCE + r'`\s*;\s*$', re.I)
SCHEMA_CONTROL = re.compile(r'^\s*(?:CREATE|DROP|ALTER|RENAME)\s+(?:DATABASE|SCHEMA)\b|^\s*USE\b', re.I)
FORBIDDEN = re.compile(r'^\s*(?:CREATE\s+USER|GRANT\b|REVOKE\b|LOAD\s+DATA|SOURCE\s+|\\\.|SELECT\b.*\bINTO\s+(?:OUTFILE|DUMPFILE))', re.I)
QUALIFIED_SOURCE = re.compile(r'`?' + SOURCE + r'`?\s*\.\s*`?[A-Za-z_]', re.I)


def inspect(source, expected_sha256=EXPECTED_SHA256):
    source = Path(source)
    if source.name != EXPECTED_NAME:
        raise ValueError('Unexpected backup identity')
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError('Backup SHA-256 mismatch')
    structural = verify(source)
    if structural['status'] != 'STRUCTURALLY_VERIFIED':
        raise ValueError('Backup structure unavailable')
    create_count = use_count = 0
    output = []
    for line in source.read_text(encoding='utf-8-sig').splitlines(keepends=True):
        stripped = line.strip()
        if FORBIDDEN.search(line) or QUALIFIED_SOURCE.search(line):
            raise ValueError('Forbidden or source-qualified SQL')
        if SCHEMA_CONTROL.match(line):
            if match := CREATE.match(stripped):
                create_count += 1
                # The recovery database must already exist and pass a separate
                # empty-schema identity check. The restore must never create it.
                line = ''
            elif USE.match(stripped):
                use_count += 1
                line = 'USE `' + RECOVERY + '`;\n'
            else:
                raise ValueError('Unexpected schema-selection SQL')
        output.append(line)
    if (create_count, use_count) != (1, 1):
        raise ValueError('Expected exactly one CREATE DATABASE and one USE')
    rewritten = ''.join(output)
    if re.search(r'^\s*USE\s+`?' + SOURCE + r'`?', rewritten, re.I | re.M):
        raise ValueError('Original database still selected')
    return rewritten, {'status': 'SAFE_TO_RETARGET',
                       'source_sha256': expected_sha256, 'database': RECOVERY,
                       'create_database_removed': create_count,
                       'use_rewrites': use_count, 'executed': False}


def prepare(source, target, expected_sha256=EXPECTED_SHA256):
    source = Path(source)
    target = Path(target)
    if source.resolve() == target.resolve() or target.exists():
        raise ValueError('Unexpected or existing output target')
    rewritten, result = inspect(source, expected_sha256)
    with target.open('x', encoding='utf-8', newline='') as stream:
        stream.write(rewritten)
    return {**result, 'status': 'PREPARED',
            'prepared_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'prepared_path': str(target.resolve())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('target', nargs='?')
    parser.add_argument('--inspect-only', action='store_true')
    args = parser.parse_args()
    try:
        if args.inspect_only:
            _, result = inspect(args.source)
        elif args.target:
            result = prepare(args.source, args.target)
        else:
            parser.error('Output target required unless --inspect-only is used')
        print(json.dumps(result, indent=2, sort_keys=True))
    except Exception as exc:
        print('Restore SQL preparation stopped: ' + type(exc).__name__)
        raise SystemExit(1)
