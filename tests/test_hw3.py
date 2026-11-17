import numpy as np
from src.hw3_evaluation import calibrate, evaluate_with_hw3


def test_calibration_uses_validation_distribution():
    a = calibrate(np.array([-10, 0, 10]), np.array([-1, 0, 1]))
    assert np.all(np.diff(a) > 0)
    assert np.all((a >= 0) & (a <= 1))


def test_hw3_evaluator_perfect_separation():
    labels = np.array([1, 1, 0, 0])
    scores = np.array([3, 2, -3, -2])
    result = evaluate_with_hw3(labels, scores, scores, 'simple')
    assert result['eer'] == 0.0
    assert result['d_prime'] > 0
    assert result['n_genuine'] == result['n_impostor'] == 2
