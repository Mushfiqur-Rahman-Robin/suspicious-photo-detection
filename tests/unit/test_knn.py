"""Unit tests: kNN consensus signal (SPEC §10.3, ED-10, P2.3)."""

from __future__ import annotations

import numpy as np

from scoring.knn import knn_consensus, knn_signal


def test_single_image_has_zero_consensus():
    matrix = np.array([[-1.0]])
    np.testing.assert_allclose(knn_consensus(matrix, 5), np.array([0.0]))


def test_self_is_never_selected_as_neighbour():
    # diagonal is the excluded -1.0 (as produced by cosine_similarity_matrix)
    matrix = np.array([[-1.0, 0.8], [0.8, -1.0]])
    np.testing.assert_allclose(knn_consensus(matrix, 1), np.array([0.8, 0.8]))


def test_k_is_clamped_to_n_minus_one():
    matrix = np.array([[0.0, 0.3, 0.5], [0.3, 0.0, 0.4], [0.5, 0.4, 0.0]])
    result = knn_consensus(matrix, 100)  # larger than N-1
    np.testing.assert_allclose(result, np.array([0.4, 0.35, 0.45]))


def test_tight_cluster_has_high_consensus():
    matrix = np.array(
        [
            [0.0, 0.9, 0.9, 0.1],
            [0.9, 0.0, 0.9, 0.1],
            [0.9, 0.9, 0.0, 0.1],
            [0.1, 0.1, 0.1, 0.0],
        ]
    )
    consensus = knn_consensus(matrix, 2)
    assert float(consensus[0]) > 0.8  # member of a tight cluster
    assert float(consensus[3]) < 0.2  # isolated point


def test_knn_signal_is_one_minus_consensus():
    matrix = np.array([[0.0, 0.8], [0.8, 0.0]])
    np.testing.assert_allclose(knn_signal(matrix, 1), np.array([0.2, 0.2]))
