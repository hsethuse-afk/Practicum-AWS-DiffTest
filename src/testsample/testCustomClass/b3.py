"""
b3.py — Refactored implementation of zscore normalization.

This module provides the same interface and behavior as `a3.py:zscore`,
but the internals are slightly refactored (non-functional change).
"""

from __future__ import annotations

import numpy as np


__all__ = ["zscore"]


def _as_keepdims_shape(shape, axis):
    """
    Compute a shape tuple that keeps reduced axes as size-1, for broadcasting.
    """
    if isinstance(axis, int):
        axis = (axis,)
    axis = tuple(ax % len(shape) for ax in axis)
    out = list(shape)
    for ax in range(len(out)):
        if ax in axis:
            out[ax] = 1
    return tuple(out)


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

    # Refactor: compute statistics without keepdims, then reshape once
    mean = np.mean(x, axis=axis, keepdims=False)
    std = np.std(x, axis=axis, ddof=ddof, keepdims=False)

    # Reshape stats to broadcast over x
    if isinstance(axis, int):
        axis_tuple = (axis,)
    else:
        axis_tuple = tuple(axis)

    # Normalize negative axes
    axis_tuple = tuple(ax % x.ndim for ax in axis_tuple)

    # Create a keepdims-like shape for broadcasting
    bdcast_shape = _as_keepdims_shape(x.shape, axis_tuple)
    mean_bd = mean.reshape(bdcast_shape)
    std_bd = std.reshape(bdcast_shape)

    # Guard against near-zero std
    std_bd = np.maximum(std_bd, eps)

    # Use out-parameters to emphasize refactoring differences
    z = np.empty_like(x, dtype=np.result_type(x, np.float64))
    np.subtract(x, mean_bd, out=z, casting="unsafe")
    np.divide(z, std_bd, out=z, casting="unsafe")

    if keepdims:
        mean_out = mean_bd
        std_out = std_bd
    else:
        mean_out = mean
        std_out = std

    if return_stats:
        return z, mean_out, std_out
    return z
