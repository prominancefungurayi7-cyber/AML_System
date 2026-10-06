"""Stage 6 fixed-model candidate feature ablation on development data only."""
from __future__ import annotations

import json
import time

import numpy as np

from contracts import ROOT, write_json
from feature_pipeline import FEATURE_NAMES
from improve_candidates import fit, SEED, DOMAINS, FAMILIES, NORMALS
from model_metrics import metrics, positive_recall_slices, false_positive_slices
from run_stage4 import protected, v2_inputs
from stage6_candidate_features import NAMES, GROUPS, extract_development
from train_candidates import load_matrix, validation_metadata, prep_for, probabilities


SPEC = {'name': 's5_gradient_boosting_060', 'algorithm': 'gradient_boosting',
        'prep': 'clipped', 'weight': 4.0,
        'params': {'learning_rate': .07, 'max_depth': 3, 'min_samples_leaf': 10,
                   'min_samples_split': 20, 'n_estimators': 180, 'subsample': .8}}


def main():
    output = ROOT / 'reports/stage6_ablation_results.json'
    if output.exists():
        raise FileExistsError(output)
    before, inputs = protected(), v2_inputs()
    started = time.perf_counter()
    Xtr, ytr, idtr = load_matrix('train')
    Xv, yv, idv = load_matrix('validation')
    Ctr, cidtr = extract_development('train')
    Cv, cidv = extract_development('validation')
    if cidtr != idtr.tolist() or cidv != idv.tolist():
        raise ValueError('Candidate feature row IDs differ from frozen Stage 3 rows')
    Ctr, Cv = np.asarray(Ctr), np.asarray(Cv)
    if Ctr.shape != (60000, 8) or Cv.shape != (15000, 8):
        raise ValueError('Unexpected candidate feature shape')
    if not np.isfinite(Ctr).all() or not np.isfinite(Cv).all():
        raise ValueError('Nonfinite candidate feature')
    metadata = validation_metadata(idv)
    configurations = {'baseline_30': []}
    configurations.update({f'plus_{name}': names for name, names in GROUPS.items()})
    configurations['plus_all_8'] = NAMES
    results = {}
    for name, features in configurations.items():
        indices = [NAMES.index(f) for f in features]
        A = np.column_stack((Xtr, Ctr[:, indices])) if indices else Xtr
        B = np.column_stack((Xv, Cv[:, indices])) if indices else Xv
        # Preserve the exact Stage 5 clipping policy on the original 30 columns.
        pre = prep_for('clipped')
        A, B = pre.fit_transform(A), pre.transform(B)
        model, warnings = fit(SPEC, A, ytr, SEED)
        train = metrics(ytr, probabilities(model, A))
        prob = probabilities(model, B)
        validation = metrics(yv, prob)
        pred = (prob >= .5).astype(np.uint8)
        results[name] = {'features': FEATURE_NAMES + features,
                         'train': train, 'validation': validation,
                         'domain_recall': positive_recall_slices(yv, pred, metadata, 'primary_domain', DOMAINS),
                         'family_recall': positive_recall_slices(yv, pred, metadata, 'primary_family', FAMILIES),
                         'normal_false_positive_rate': false_positive_slices(yv, pred, metadata, NORMALS),
                         'convergence_warnings': warnings}
        print(name, round(validation['macro_f1'], 4), round(validation['suspicious_recall'], 4), flush=True)
    after, inputs_after = protected(), v2_inputs()
    if before != after or inputs != inputs_after:
        raise RuntimeError('Protected files or frozen V2 inputs changed')
    write_json(output, {'seed': SEED, 'threshold': .5, 'spec': SPEC,
                        'candidate_names': NAMES, 'results': results,
                        'elapsed_seconds': time.perf_counter() - started,
                        'protection': {'result': 'PASS', 'protected_file_count': len(before),
                                       'v2_input_file_count': len(inputs)}})
    print(output, flush=True)


if __name__ == '__main__':
    main()
