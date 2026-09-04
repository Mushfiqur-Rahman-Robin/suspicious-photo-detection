"""Unit tests: L2 normalization helper (ED-2)."""

from __future__ import annotations

import numpy as np

from embedding.normalize import l2_normalize


def test_rows_are_unit_norm():
    vectors = np.array([[3.0, 4.0], [1.0, 0.0]])
    normalized = l2_normalize(vectors)
    np.testing.assert_allclose(np.linalg.norm(normalized, axis=1), np.ones(2))


def test_direction_is_preserved():
    vectors = np.array([[3.0, 4.0]])
    normalized = l2_normalize(vectors)
    np.testing.assert_allclose(normalized, np.array([[0.6, 0.8]]))


def test_zero_rows_stay_zero():
    vectors = np.array([[0.0, 0.0], [1.0, 0.0]])
    normalized = l2_normalize(vectors)
    np.testing.assert_allclose(normalized[0], np.zeros(2))
    assert not np.isnan(normalized).any()


def test_empty_matrix_returns_empty():
    normalized = l2_normalize(np.zeros((0, 3)))
    assert normalized.shape == (0, 3)


def test_dtype_is_preserved():
    vectors = np.array([[1.0, 0.0]], dtype=np.float32)
    assert l2_normalize(vectors).dtype == np.float32
