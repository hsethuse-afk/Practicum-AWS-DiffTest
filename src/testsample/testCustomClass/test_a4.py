#!/usr/bin/env python3
"""
test_a3.py — Executable tests for a3.zscore

Run:
    python test_a3.py
"""
from typing import Self

import unittest
import numpy as np

import a4


class TestZScoreA4(unittest.TestCase):
    def test_basic_shape_and_zero_mean_unit_std_axis0(self: Self) -> None:
        rng = np.random.default_rng(0)
        x = rng.normal(size=(10, 5))
        z, m, s = a4.zscore(
            x, axis=0, return_stats=True, keepdims=False
        )
        self.assertEqual(z.shape, x.shape)
        # Means should be ~0 and stds ~1
        self.assertTrue(
            np.allclose(np.mean(z, axis=0), 0.0, atol=1e-12)
        )
        self.assertTrue(np.allclose(np.std(z, axis=0), 1.0, atol=1e-12))
        # Sanity: stats match numpy's
        self.assertTrue(np.allclose(m, np.mean(x, axis=0)))
        self.assertTrue(np.allclose(s, np.std(x, axis=0)))

    def test_axis1_keepdims(self: Self) -> None:
        rng = np.random.default_rng(1)
        x = rng.uniform(-3, 3, size=(7, 11))
        z, m, s = a4.zscore(x, axis=1, keepdims=True, return_stats=True)
        self.assertEqual(z.shape, x.shape)
        self.assertEqual(m.shape, (7, 1))
        self.assertEqual(s.shape, (7, 1))
        self.assertTrue(
            np.allclose(
                np.mean(z, axis=1, keepdims=True), 0.0, atol=1e-12
            )
        )
        self.assertTrue(
            np.allclose(
                np.std(z, axis=1, keepdims=True), 1.0, atol=1e-12
            )
        )

    def test_ddof(self: Self) -> None:
        rng = np.random.default_rng(2)
        x = rng.normal(size=(4, 6, 8))
        z, m, s = a4.zscore(
            x, axis=(0, 2), ddof=1, keepdims=False, return_stats=True
        )
        # Check stats agree with numpy using ddof=1
        self.assertTrue(np.allclose(m, np.mean(x, axis=(0, 2))))
        self.assertTrue(np.allclose(s, np.std(x, axis=(0, 2), ddof=1)))
        # Reconstruct x from z, m, s: x ≈ z*s + m (with broadcasting via new axes)
        # Expand m and s for broadcasting
        m_bd = np.expand_dims(m, axis=1)
        s_bd = np.expand_dims(s, axis=1)
        x_rec = z * s_bd + m_bd
        self.assertTrue(np.allclose(x, x_rec, atol=1e-9))

    def test_eps_guard(self: Self) -> None:
        x = np.array([[1.0, 1.0, 1.0]])
        z, m, s = a4.zscore(
            x, axis=1, keepdims=True, return_stats=True, eps=1e-9
        )
        # std is clamped by eps, so z should be all zeros (since x == mean)
        self.assertTrue(np.allclose(z, 0.0))
        self.assertTrue(np.allclose(m, [[1.0]]))
        self.assertTrue(np.all(s >= 1e-9))

    def test_input_validation(self: Self) -> None:
        with self.assertRaises(ValueError):
            a4.zscore(np.array([]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
