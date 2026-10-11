"""Current frozen-asset gate; original historical snapshots remain untouched."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = {
    'ml_v4/evidence/integration_stage2/before_sha256.json':
        'd1fb80ae3d452fdf79987ba833de8004e93699cb11f496cd5e0d464d40ba21f8',
    'ml_v4/evidence/integration_stage2a/before_sha256.json':
        '5344955eb4000989b0d3bc70aa26da3742a18ee020d9532c03fa69374ba15c04',
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_original_historical_manifests_are_unchanged():
    for path, expected in HISTORICAL.items():
        assert sha(path) == expected, path


def test_current_frozen_v4_and_legacy_model_assets_match_authority():
    authority = json.loads((ROOT / 'ml_v4/frozen_inference/authority.json').read_text())
    history = json.loads((ROOT / 'ml_v4/frozen_inference/history_authority.json').read_text())
    for record in authority['artifacts'].values():
        assert sha(record['path']) == record['sha256'], record['path']
    for path, expected in history.items():
        assert sha(path) == expected, path
    historical = json.loads((ROOT / 'ml_v4/evidence/integration_stage2/before_sha256.json').read_text())
    legacy_model = 'ml/stage14/stage14_frozen_model.pkl'
    assert sha(legacy_model) == historical[legacy_model]
