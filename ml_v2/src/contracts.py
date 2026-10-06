"""V2-only filesystem, serialization and development access contracts (stdlib)."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTITIONS = ('train', 'validation', 'final_test', 'independent')
DEVELOPMENT = ('train', 'validation')
EVENT_FIELDS = 'transaction_id event_sequence event_timestamp sender_wallet receiver_wallet amount_minor currency transaction_type channel agent_id serviced_wallet agent_flow_direction'.split()
TRUTH_FIELDS = 'transaction_id target primary_domain primary_family episode_id normal_family normal_episode_id signal_strength episode_phase label_basis'.split()
WALLET_FIELDS = 'wallet_id customer_id partition profile_type activity_band initial_balance_minor activation_timestamp'.split()
AGENT_FIELDS = 'agent_id partition activity_band initial_float_minor activation_timestamp'.split()
BASIS = 'precommitted_scenario_membership_v2'


def safe_path(path: str | Path) -> Path:
    """Validate lexical and resolved ancestry, rejecting every link/reparse point."""
    p = Path(os.path.abspath(path))
    if not p.is_relative_to(ROOT) or p == ROOT:
        raise ValueError('Output/access path must be strictly inside ml_v2')
    if ROOT.is_symlink() or ROOT.is_junction():
        raise ValueError('V2 root cannot be a link/junction')
    node = ROOT
    for part in p.relative_to(ROOT).parts:
        node = node / part
        if node.is_symlink() or node.is_junction():
            raise ValueError('Links/junctions are forbidden in V2 paths')
    if not p.resolve().is_relative_to(ROOT):
        raise ValueError('Resolved path escapes V2')
    return p


def write_json(path, value):
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write('\n')


def write_csv(path, fields, rows):
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with safe_path(path).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def partition_path(dataset_root, partition):
    if partition not in PARTITIONS:
        raise ValueError('Unknown partition')
    return safe_path(Path(dataset_root) / ('development' if partition in DEVELOPMENT else 'holdout') / partition)


def load_development(dataset_root, partition, table='transactions'):
    """Only supported entry point for future development/training data access.

    This is an application guard, not an OS sandbox against arbitrary Python I/O.
    No holdout override parameter exists.
    """
    if partition not in DEVELOPMENT:
        raise PermissionError('Training/development access is limited to train and validation')
    if table not in ('transactions', 'ground_truth', 'wallets', 'agents'):
        raise ValueError('Unknown table')
    root = safe_path(dataset_root)
    manifest = json.loads((root / 'manifests/generation_manifest.json').read_text(encoding='utf-8'))
    if manifest['partition_roles'].get(partition) != 'development':
        raise PermissionError('Manifest does not authorize development access')
    p = partition_path(root, partition) / f'{table}.csv'
    rel = p.relative_to(root).as_posix()
    if digest(p) != manifest['file_hashes'][rel]:
        raise ValueError('Dataset hash mismatch')
    return read_csv(p)
