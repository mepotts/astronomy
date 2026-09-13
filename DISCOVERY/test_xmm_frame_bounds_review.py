"""Independent scalar oracle and realizable synthetic-frame allocation checks."""

import unittest

import numpy as np
from xmm_frame_bounds import FrameBounds


def scalar_union(intervals):
    result = []
    for start, stop in sorted(map(tuple, intervals)):
        if result and start <= result[-1][1]:
            result[-1][1] = max(stop, result[-1][1])
        else:
            result.append([start, stop])
    return result


def scalar_accepted(query, gtis):
    return scalar_union([[max(a, c), min(b, d)] for a, b in query for c, d in gtis
                         if max(a, c) < min(b, d)])


class IndependentFrameTests(unittest.TestCase):
    def test_scalar_oracle_and_physical_allocations(self):
        rng = np.random.default_rng(913)
        for _ in range(100):
            # Variable-duration, non-overlapping physical frames; independently
            # drop some retained rows. Uniform integration is only a synthetic
            # example of an admissible allocation, not assumed by the method.
            durations = rng.uniform(0.3, 6, 30)
            ends = np.cumsum(durations)
            starts = ends - durations
            keep = rng.random(30) > 0.25
            starts, ends, durations = starts[keep], ends[keep], durations[keep]
            centres = (starts + ends) / 2
            weights = durations * rng.uniform(0, 1, len(durations))
            query = np.sort(rng.uniform(-5, ends[-1] + 5, (5, 2)), axis=1)
            gtis = np.sort(rng.uniform(-5, ends[-1] + 5, (4, 2)), axis=1)
            accepted = scalar_accepted(query, gtis)
            lower = upper = allocation = 0.0
            for n, weight in enumerate(weights):
                left = centres[n - 1] if n else -np.inf
                right = centres[n + 1] if n + 1 < len(centres) else np.inf
                if any(a <= left and right <= b for a, b in accepted):
                    lower += weight
                if any(max(a, left) < min(b, right) for a, b in accepted):
                    upper += weight
                overlap = sum(max(0, min(ends[n], b) - max(starts[n], a)) for a, b in accepted)
                allocation += weight * overlap / durations[n]
            for chunk in (1, 7, 100):
                measured = FrameBounds(centres, weights, chunk_size=chunk).bounds(query, gtis)
                self.assertAlmostEqual(measured['lower_exposure_s'], lower, places=10)
                self.assertAlmostEqual(measured['upper_exposure_s'], upper, places=10)
                self.assertLessEqual(lower, allocation + 1e-10)
                self.assertLessEqual(allocation, upper + 1e-10)


if __name__ == '__main__':
    unittest.main()
