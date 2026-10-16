"""Read-only model contributions for one already recorded V4 decision."""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LABELS = {
    'wallet_pass_through_fraction_24h': 'Wallet pass-through share over 24 hours',
    'prior_return_path_count_7d': 'Prior return paths over 7 days',
    'wallet_prior_funding_residual_minor_24h': 'Prior funding residual over 24 hours',
    'wallet_activity_acceleration_1h': 'Change in wallet activity over 1 hour',
    'current_to_selected_path_first_value_ratio': 'Current amount relative to the first payment in the selected path',
}


def evidence(transaction_id):
    import numpy as np
    import xgboost as xgb
    from ml_v4.frozen_inference.cli import connection
    from ml_v4.frozen_inference.history import verified_snapshot
    from ml_v4.frozen_inference.service import FrozenModel, Failure
    from v4_shadow import MODEL, FEATURE

    conn = connection()
    try:
        events, context = verified_snapshot(conn, transaction_id)
        stored = conn.execute(
            'SELECT status,prediction,suspicious_probability FROM v4_shadow_results '
            'WHERE transaction_id=? AND model_version=? AND feature_version=?',
            (transaction_id, MODEL, FEATURE),
        ).fetchone()
        if not stored or stored['status'] != 'success':
            raise ValueError('No successful recorded V4 decision for this transaction')
        model = FrozenModel()
        features, _ = model.replay(events, transaction_id)
        encoded = model.pre.transform(features)
        probability = model.predict(features)
        if abs(probability - float(stored['suspicious_probability'])) > 1e-6:
            raise Failure('INFERENCE_ERROR')
        if int(probability >= 0.5) != stored['prediction']:
            raise Failure('INFERENCE_ERROR')
        columns = list(model.pre.output_columns_)
        contributions = model.est.get_booster().predict(
            xgb.DMatrix(encoded, feature_names=columns), pred_contribs=True
        )[0]
        if len(contributions) != len(columns) + 1 or not np.isfinite(contributions).all():
            raise Failure('INFERENCE_ERROR')
        reconstructed = 1 / (1 + math.exp(-float(contributions.sum())))
        if abs(reconstructed - probability) > 1e-5:
            raise Failure('INFERENCE_ERROR')
        ranked = sorted(zip(columns, contributions[:-1]), key=lambda pair: abs(pair[1]), reverse=True)
        findings = [
            {'feature': name, 'label': LABELS.get(name, name.replace('_', ' ')),
             'direction': 'raises the suspicious score' if value > 0 else 'lowers the suspicious score',
             'contribution': round(float(value), 3)}
            for name, value in ranked[:5] if abs(value) >= 0.01
        ]
        return {'transaction_id': transaction_id, 'probability': probability,
                'prediction': stored['prediction'], 'source_revision': context['source_revision'],
                'findings': findings}
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        raise SystemExit('usage: v4_model_evidence.py TRANSACTION_ID')
    print(json.dumps(evidence(int(sys.argv[1])), allow_nan=False))
