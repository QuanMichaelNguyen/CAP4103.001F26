"""Adapter to the *unchanged* HW3 Evaluator class supplied with the assignment.

HW3 expects bounded [0, 1] similarities and evaluates a fixed threshold grid.
The project's distance scores are higher-is-better but unbounded, so calibrate
using validation scores only before invoking the HW3 evaluator.
"""
from __future__ import annotations
from pathlib import Path
import re
import numpy as np
from hw3.main import Evaluator


def calibrate(scores, validation_scores):
    """Validation-only affine standardization followed by a monotone logistic map."""
    ref = np.asarray(validation_scores, dtype=float)
    scores = np.asarray(scores, dtype=float)
    sd = float(np.std(ref))
    z = (scores - float(np.mean(ref))) / (sd if sd > 1e-10 else 1.0)
    return 1.0 / (1.0 + np.exp(-np.clip(z, -50.0, 50.0)))


def evaluate_with_hw3(labels, scores, validation_scores, title, output=None, plots=False,
                      num_thresholds=2001):
    """Evaluate actual genuine/impostor trials with course-provided HW3 code.

    HW3's fixed sampled threshold grid produces an approximate EER. The project
    also calculates an empirical-threshold EER independently for comparison.
    """
    labels = np.asarray(labels)
    values = calibrate(scores, validation_scores)
    genuine, impostor = values[labels == 1], values[labels == 0]
    if len(genuine) == 0 or len(impostor) == 0:
        raise ValueError('Both genuine and impostor scores are required')
    safe_title = re.sub(r'[^a-zA-Z0-9_-]+', '_', title)
    evaluator = Evaluator(num_thresholds, genuine, impostor, safe_title)
    fpr, fnr, tpr = evaluator.compute_rates()
    eer, threshold = evaluator.get_EER(fpr, fnr)
    result = {'eer': float(eer), 'threshold': float(threshold),
              'd_prime': float(evaluator.get_dprime()),
              'far_at_eer': float(fpr[np.argmin(abs(np.asarray(fpr)-np.asarray(fnr)))]),
              'frr_at_eer': float(fnr[np.argmin(abs(np.asarray(fpr)-np.asarray(fnr)))]),
              'n_genuine': int(len(genuine)), 'n_impostor': int(len(impostor)),
              'score_calibration': 'validation-standardized logistic [0, 1]',
              'method': 'course HW3 Evaluator; 2001 fixed thresholds in [-0.1, 1.1]'}
    if plots:
        # HW3 plot methods save relative filenames. Work in destination only
        # for the brief plotting call and always restore original cwd.
        import os
        out = Path(output or '.').resolve()
        out.mkdir(parents=True, exist_ok=True)
        old = Path.cwd()
        try:
            os.chdir(out)
            evaluator.plot_score_distribution()
            evaluator.plot_det_curve(fpr, fnr)
            evaluator.plot_roc_curve(fpr, tpr)
        finally:
            os.chdir(old)
    return result
