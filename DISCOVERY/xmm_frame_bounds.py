"""Pure numerical bounds under unvalidated centred, non-overlapping-frame assumptions.

No I/O and no physical calibration. Envelope width is never exposure. Floating
summation uses ordinary float64 arithmetic, not certified interval arithmetic.
"""

import math

import numpy as np


def _numeric(values, name):
    if isinstance(values, (list, tuple)) and any(
        isinstance(value, (bool, np.bool_)) for value in np.asarray(values, dtype=object).flat
    ):
        raise ValueError(f"{name} must not contain booleans")
    array = np.asarray(values)
    if array.dtype.kind not in "iuf":
        raise ValueError(f"{name} must be real numeric values, not booleans or objects")
    array = np.array(array, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    return array


def _union(values):
    rows = _numeric(values, "Intervals")
    if rows.shape in ((0,), (0, 2)):
        return np.empty((0, 2), dtype=np.float64)
    if rows.ndim != 2 or rows.shape[1] != 2 or np.any(rows[:, 0] >= rows[:, 1]):
        raise ValueError("Intervals must have shape (n, 2) with start < stop")
    rows = rows[np.argsort(rows[:, 0], kind="stable")]
    result = [rows[0].copy()]
    for start, stop in rows[1:]:
        if start <= result[-1][1]:
            result[-1][1] = max(stop, result[-1][1])
        else:
            result.append(np.array([start, stop]))
    return np.asarray(result)


def _intersection(left, right):
    """Intersect two disjoint ordered unions in linear interval-count time."""
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        start = max(left[i, 0], right[j, 0])
        stop = min(left[i, 1], right[j, 1])
        if start < stop:
            result.append([start, stop])
        if left[i, 1] <= right[j, 1]:
            i += 1
        else:
            j += 1
    return np.asarray(result, dtype=np.float64).reshape(-1, 2)


class FrameBounds:
    """Prepare one CCD/exposure's centres and full-frame weights once.

    For interior row f support is [centre[f-1], centre[f+1]); the first/last
    exterior side is unbounded. Arrays are copied, so caller mutation cannot
    change a prepared query. No support assumption is established by validation.
    """

    def __init__(self, centres, weights, chunk_size=262144):
        self.centres = _numeric(centres, "Centres")
        self.weights = _numeric(weights, "Weights")
        if (self.centres.ndim != 1 or self.weights.shape != self.centres.shape
                or np.any(self.centres[1:] <= self.centres[:-1])
                or np.any(self.weights < 0)):
            raise ValueError("Require ordered distinct centres and matching nonnegative weights")
        if (isinstance(chunk_size, (bool, np.bool_))
                or not isinstance(chunk_size, (int, np.integer)) or chunk_size <= 0):
            raise ValueError("chunk_size must be a positive integer")
        self.chunk_size = int(chunk_size)
        self.centres.flags.writeable = False
        self.weights.flags.writeable = False

    def bounds(self, accepted_intervals, gtis):
        """Bound weight in the intersection of accepted-time and GTI unions.

        The caller supplies disjoint accepted whole reference bins outside its
        fixed exclusion. This routine also unions overlapping input intervals,
        so a frame is counted at most once per query, including disconnected J.
        It cannot verify how the caller chose its accepted intervals.
        """
        accepted = _intersection(_union(accepted_intervals), _union(gtis))
        n = len(self.centres)
        lower_parts, upper_parts = [], []
        contained_count = intersecting_count = 0
        if len(accepted):
            for start in range(0, n, self.chunk_size):
                stop = min(n, start + self.chunk_size)
                index = np.arange(start, stop)
                low = self.centres[np.maximum(index - 1, 0)].copy()
                high = self.centres[np.minimum(index + 1, n - 1)].copy()
                low[index == 0] = -np.inf
                high[index == n - 1] = np.inf

                # First interval ending strictly after low can positively
                # intersect only if it also starts strictly before high.
                after = np.searchsorted(accepted[:, 1], low, side="right")
                clipped_after = np.minimum(after, len(accepted) - 1)
                overlaps = ((after < len(accepted))
                            & (accepted[clipped_after, 0] < high))

                # Since adjacent intervals were unioned, full containment must
                # hold within one component, not across a missing-time gap.
                before = np.searchsorted(accepted[:, 0], low, side="right") - 1
                contained = ((before >= 0)
                             & (accepted[np.maximum(before, 0), 1] >= high))
                contained_count += int(np.count_nonzero(contained))
                intersecting_count += int(np.count_nonzero(overlaps))
                weights = self.weights[start:stop]
                with np.errstate(over="ignore", invalid="ignore"):
                    lower_parts.append(float(np.sum(weights[contained], dtype=np.float64)))
                    upper_parts.append(float(np.sum(weights[overlaps], dtype=np.float64)))
        try:
            lower, upper = math.fsum(lower_parts), math.fsum(upper_parts)
        except OverflowError as exc:
            raise ValueError("Exposure-weight sum overflow") from exc
        if not math.isfinite(lower) or not math.isfinite(upper):
            raise ValueError("Exposure-weight sum overflow")
        return {
            "status": "MATHEMATICAL_BOUNDS_SUPPORT_ASSUMED",
            "lower_exposure_s": lower,
            "upper_exposure_s": upper,
            "frame_count": n,
            "fully_contained_frames": contained_count,
            "uncertain_frames": intersecting_count - contained_count,
            "outside_frames": n - intersecting_count,
            "accepted_gti_intervals": len(accepted),
            "endpoint_policy": "first_left_unbounded_last_right_unbounded",
            "floating_arithmetic": "float64_not_certified_interval_arithmetic",
        }


def exposure_bounds(centres, weights, accepted_intervals, gtis, chunk_size=262144):
    """Convenience one-query interface; reuse FrameBounds for repeated queries."""
    return FrameBounds(centres, weights, chunk_size).bounds(accepted_intervals, gtis)
