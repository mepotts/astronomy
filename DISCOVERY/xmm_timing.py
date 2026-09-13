"""Synthetic-tested primitives for a later frozen counts-control experiment.

No file or network access. A constant total-aperture-rate diagnostic is not
background-subtracted source significance or an astrophysical false-alarm rate.
"""

import numpy as np
from scipy.stats import binom


def edges_checked(edges):
    edges = np.asarray(edges, dtype=float)
    if edges.ndim != 1 or len(edges) < 2 or not np.all(np.isfinite(edges)) or np.any(np.diff(edges) <= 0):
        raise ValueError("Invalid bin edges")
    return edges


def interval_union(intervals):
    intervals = np.asarray(intervals, dtype=float)
    if intervals.shape in ((0,), (0, 2)):
        return np.empty((0, 2), dtype=float)
    if (intervals.ndim != 2 or intervals.shape[1] != 2 or not np.all(np.isfinite(intervals))
            or np.any(intervals[:, 1] <= intervals[:, 0])):
        raise ValueError("Invalid good-time intervals")
    rows = intervals[np.argsort(intervals[:, 0], kind="stable")]
    merged = [rows[0].copy()]
    for start, stop in rows[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(stop, merged[-1][1])
        else:
            merged.append(np.array([start, stop]))
    return np.asarray(merged)


def wall_coverage(edges, intervals):
    """GTI wall-clock duration per bin, not detector live/effective exposure."""
    edges = edges_checked(edges)
    result = np.zeros(len(edges) - 1)
    for start, stop in interval_union(intervals):
        result += np.maximum(0, np.minimum(edges[1:], stop) - np.maximum(edges[:-1], start))
    return result


def half_open_counts(times, edges):
    """Return integer counts and number outside [first edge, final edge)."""
    edges = edges_checked(edges)
    times = np.asarray(times, dtype=float)
    if times.ndim != 1 or not np.all(np.isfinite(times)):
        raise ValueError("Invalid event times")
    index = np.searchsorted(edges, times, side="right") - 1
    valid = (index >= 0) & (index < len(edges) - 1)
    return np.bincount(index[valid], minlength=len(edges) - 1), int(np.count_nonzero(~valid))


def reference_mask(edges, tested_bin, accepted, exclusion_seconds=1000.0):
    """Select entire accepted bins outside the prescribed exclusion interval."""
    edges = edges_checked(edges)
    accepted = np.asarray(accepted)
    if accepted.dtype != np.dtype(bool) or accepted.shape != (len(edges) - 1,):
        raise ValueError("Invalid acceptance mask")
    if (isinstance(tested_bin, (bool, np.bool_)) or not isinstance(tested_bin, (int, np.integer))
            or not 0 <= tested_bin < len(accepted)
            or not np.isfinite(exclusion_seconds) or exclusion_seconds < 0):
        raise ValueError("Invalid reference selection")
    return accepted & ((edges[1:] <= edges[tested_bin] - exclusion_seconds)
                       | (edges[:-1] >= edges[tested_bin + 1] + exclusion_seconds))


def constant_rate_tail(count, reference_count, exposure, reference_exposure):
    """One-sided conditional Poisson-rate diagnostic with fixed exposures.

Conditions on the two counts' sum. Assumes independent Poisson counts and a
common total-aperture rate under the null. Variable background or unmodelled
exposure changes invalidate an intrinsic-source interpretation.
"""
    for value in (count, reference_count):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 0:
            raise ValueError("Counts must be nonnegative integers")
    if any(isinstance(value, (bool, np.bool_)) for value in (exposure, reference_exposure)):
        raise ValueError("Exposures must be measured seconds, not booleans")
    exposure, reference_exposure = float(exposure), float(reference_exposure)
    if (not np.isfinite(exposure) or not np.isfinite(reference_exposure)
            or exposure <= 0 or reference_exposure <= 0):
        raise ValueError("Positive measured exposures required")
    total_exposure = exposure + reference_exposure
    if not np.isfinite(total_exposure):
        raise ValueError("Exposure sum overflow")
    probability = exposure / total_exposure
    return float(binom.sf(int(count) - 1, int(count) + int(reference_count), probability))


def bounded_constant_rate_tail(count, reference_count, exposure_bounds, reference_bounds):
    """Worst-case positive-excess tail under valid effective-exposure bounds.

    The bin/reference time selections and counts must be disjoint and fixed.
    Bounds must enclose their actual applicable exposures; this function does
    not establish frame support, spatial stability or Poisson assumptions.
    Zero lower exposure is unmeasured and raises, never a significance value.
    The reference-duration eligibility threshold is a separate protocol gate.
    """
    validated = []
    for bounds in (exposure_bounds, reference_bounds):
        raw = np.asarray(bounds, dtype=object)
        if raw.shape != (2,) or any(isinstance(v, (bool, np.bool_)) for v in raw.flat):
            raise ValueError("Expected two measured exposure bounds")
        values = np.asarray(bounds, dtype=float)
        if not np.all(np.isfinite(values)) or values[0] <= 0 or values[1] < values[0]:
            raise ValueError("Positive ordered exposure bounds required")
        validated.append(values)
    # P[X >= count | total] is nondecreasing in p. The largest admissible
    # p uses the bin upper and reference lower exposure, even if that pair
    # is unattainable because of shared boundary-frame uncertainty.
    return constant_rate_tail(count, reference_count, validated[0][1], validated[1][0])
