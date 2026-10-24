"""Read-only model contributions for one already recorded V4 decision."""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def recorded_decision(conn, transaction_id):
    """Use the effective audited result, preserving the original error record."""
    from v4_shadow import get, validate
    stored = get(conn, transaction_id)
    if stored and stored['status'] == 'inference_error':
        retry = conn.execute(
            "SELECT result_body FROM v4_primary_attempt_events WHERE transaction_id=? "
            "AND event_kind='COMPLETED' AND outcome='success' ORDER BY event_id DESC LIMIT 1",
            (transaction_id,)).fetchone()
        if retry:
            stored = json.loads(retry['result_body'])
    if not stored or stored['status'] != 'success':
        raise ValueError('No successful recorded V4 decision for this transaction')
    return validate(stored, transaction_id)

LABELS = {
    'wallet_pass_through_fraction_24h': 'How much received money was sent onwards within 24 hours',
    'prior_return_path_count_7d': 'Transfers that led money back to an earlier wallet within 7 days',
    'wallet_prior_funding_residual_minor_24h': 'The difference between money received and money sent within 24 hours',
    'wallet_activity_acceleration_1h': 'How quickly the wallet activity changed within an hour',
    'current_to_selected_path_first_value_ratio': 'How closely this amount matches an earlier transfer in the payment chain',
}


def activity_summary(events, current, contract):
    """Actual same-wallet payments up to this decision; never future activity."""
    recent = []
    for raw in events:
        event = contract.Event(**raw)
        if (event.subject == current.subject and event.key <= current.key
                and current.time - 3600 * 1000000 <= event.time):
            recent.append(event)
    recent.sort(key=lambda event: event.key)
    examples = ', '.join(
        f"{event.transaction_type.replace('_', ' ')} ${event.amount_minor / 100:,.2f}"
        for event in recent[-10:])
    total = sum(event.amount_minor for event in recent) / 100
    suffix = ' Showing the latest 10.' if len(recent) > 10 else ''
    return (f'Wallet {current.subject} made {len(recent)} payment(s) totalling '
            f'${total:,.2f} in the hour ending with this transaction: {examples}.{suffix}')


def evidence(transaction_id):
    import numpy as np
    import xgboost as xgb
    from ml_v4.frozen_inference.cli import connection
    from ml_v4.frozen_inference.history import verified_snapshot
    from ml_v4.frozen_inference.service import FrozenModel, Failure
    from v4_target_inference import replay_target

    conn = connection()
    try:
        events, context = verified_snapshot(conn, transaction_id)
        stored = recorded_decision(conn, transaction_id)
        model = FrozenModel()
        features, current = replay_target(model, events, transaction_id)
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
             'direction': 'increased concern' if value > 0 else 'reduced concern',
             'contribution': round(float(value), 3)}
            for name, value in ranked[:5] if abs(value) >= 0.01
        ]
        return {'transaction_id': transaction_id, 'probability': probability,
                'prediction': stored['prediction'], 'source_revision': context['source_revision'],
                'summary': ('Flagged by AI because the payment pattern was assessed as suspicious.'
                            if stored['prediction'] else 'The AI did not flag this payment as suspicious.'),
                'activity': activity_summary(events, current, model.contract),
                'findings': findings}
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        raise SystemExit('usage: v4_model_evidence.py TRANSACTION_ID')
    print(json.dumps(evidence(int(sys.argv[1])), allow_nan=False))
