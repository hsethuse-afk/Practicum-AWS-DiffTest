"""
a3.py — Reference implementation of zscore normalization.

This module exposes a single function `zscore` that normalizes a NumPy array
along a given axis. It is designed to share the same interface as `b3.py`,
with only minor, non‑functional refactoring differences between the two.
"""

from __future__ import annotations

import numpy as np


__all__ = ["zscore"]


def zscore(
    x: np.ndarray,
    axis: int | tuple[int, ...] = 0,
    ddof: int = 0,
    keepdims: bool = False,
    return_stats: bool = False,
    eps: float = 1e-12,
) -> np.ndarray | tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Z-score normalize an array along the specified axis.

    Parameters
    ----------
    x : np.ndarray
        Input data.
    axis : int or tuple of ints, default 0
        Axis or axes along which to compute mean and std.
    ddof : int, default 0
        Delta Degrees of Freedom used in the standard deviation.
    keepdims : bool, default False
        Whether to keep the reduced dimensions for broadcasting.
    return_stats : bool, default False
        If True, return (z, mean, std). Otherwise return only z.
    eps : float, default 1e-12
        Small constant to avoid division by zero.

    Returns
    -------
    z : np.ndarray
        Z-scored array.
    mean : np.ndarray
        Mean along `axis` (only if return_stats is True).
    std : np.ndarray
        Std along `axis` (only if return_stats is True).
    """
    x = np.asarray(x)
    if x.size == 0:
        raise ValueError("Input array 'x' must not be empty.")

    mean = np.mean(x, axis=axis, keepdims=True)
    std = np.std(x, axis=axis, ddof=ddof, keepdims=True)
    # Guard against near-zero std
    std = np.maximum(std, eps)

    z = (x - mean) / std

    if not keepdims:
        mean = np.squeeze(mean, axis=axis)
        std = np.squeeze(std, axis=axis)

    if return_stats:
        return z, mean, std
    return z
