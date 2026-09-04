"""Unit tests: cosine similarity matrix (SPEC §10.2, ED-2, P2.1)."""

from __future__ import annotations

import numpy as np
import pytest

from core.exceptions import DetectionError
from embedding.normalize import l2_normalize
from scoring.similarity import cosine_similarity_matrix


def _unit_matrix(vectors):
    return l2_normalize(np.asarray(vectors, dtype=np.float64))


def test_diagonal_is_excluded():
    matrix = cosine_similarity_matrix(_unit_matrix([[1.0, 0.0], [0.0, 1.0]]))
    assert matrix[0, 0] == -1.0
    assert matrix[1, 1] == -1.0


def test_matrix_is_symmetric():
    matrix = cosine_similarity_matrix(
        _unit_matrix([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    )
    np.testing.assert_allclose(matrix, matrix.T)


def test_identical_vectors_have_similarity_one():
    matrix = cosine_similarity_matrix(_unit_matrix([[1.0, 0.0], [1.0, 0.0]]))
    assert matrix[0, 1] == pytest.approx(1.0)


def test_orthogonal_vectors_have_similarity_zero():
    matrix = cosine_similarity_matrix(_unit_matrix([[1.0, 0.0], [0.0, 1.0]]))
    assert matrix[0, 1] == pytest.approx(0.0)


def test_opposite_vectors_have_similarity_negative_one():
    matrix = cosine_similarity_matrix(_unit_matrix([[1.0, 0.0], [-1.0, 0.0]]))
    assert matrix[0, 1] == pytest.approx(-1.0)


def test_similarities_stay_within_unit_interval():
    rng = np.random.default_rng(0)
    matrix = cosine_similarity_matrix(l2_normalize(rng.normal(size=(20, 8))))
    assert np.all(matrix >= -1.0 - 1e-9)
    assert np.all(matrix <= 1.0 + 1e-9)


def test_non_2d_input_raises():
    with pytest.raises(DetectionError):
        cosine_similarity_matrix(np.ones(8))
