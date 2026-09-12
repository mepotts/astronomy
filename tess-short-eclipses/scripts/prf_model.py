"""Synthetic-developed finite-support TESS PRF interpolation and diagnostic fits.

No file/network operations. Callers own provenance, scientific gates and budgets.
"""

import numpy as np
from scipy.optimize import least_squares

REFERENCE = 58
SAMPLING = 9
RADIUS = 59 / 9
MAX_NFEV = 120
DERIVATIVE_STEP = 1e-4


class PRFGrid:
    """Corners ordered (rowlo,collo), (rowlo,colhi), (rowhi,collo), (rowhi,colhi)."""

    def __init__(self, arrays, rows, columns, origin):
        self.arrays = np.array(arrays, dtype=float, copy=True)
        self.rows = np.array(rows, dtype=float, copy=True)
        self.columns = np.array(columns, dtype=float, copy=True)
        self.origin = np.array(origin, dtype=float, copy=True)
        if (self.arrays.shape != (4, 117, 117) or self.rows.shape != (2,)
                or self.columns.shape != (2,) or self.origin.shape != (2,)
                or not all(np.all(np.isfinite(a)) for a in (self.arrays, self.rows, self.columns, self.origin))
                or np.any(np.diff(self.rows) <= 0) or np.any(np.diff(self.columns) <= 0)):
            raise ValueError("STOP_GRID_SCHEMA")
        for array in (self.arrays, self.rows, self.columns, self.origin):
            array.flags.writeable = False

    def weights(self, x, y, corner=None):
        if not np.all(np.isfinite([x, y])):
            raise ValueError("STOP_POSITION_NONFINITE")
        column, row = self.origin + [x, y]
        if not (self.columns[0] <= column <= self.columns[1] and self.rows[0] <= row <= self.rows[1]):
            raise ValueError("STOP_FIELD_EXTRAPOLATION")
        if corner is not None:
            if type(corner) is not int or not 0 <= corner < 4:
                raise ValueError("STOP_CORNER")
            return np.eye(4)[corner]
        cx = (column - self.columns[0]) / np.diff(self.columns)[0]
        ry = (row - self.rows[0]) / np.diff(self.rows)[0]
        return np.array([(1 - ry) * (1 - cx), (1 - ry) * cx, ry * (1 - cx), ry * cx])

    def sample(self, pixel_x, pixel_y, x, y, corner=None):
        """Unnormalized detector samples, continuous zero-extended bilinear nodes."""
        weights = self.weights(x, y, corner)
        px, py = np.broadcast_arrays(np.asarray(pixel_x, dtype=float), np.asarray(pixel_y, dtype=float))
        if not np.all(np.isfinite(px)) or not np.all(np.isfinite(py)):
            raise ValueError("STOP_PIXEL_COORDINATES")
        ux, uy = REFERENCE + SAMPLING * (px - x), REFERENCE + SAMPLING * (py - y)
        # Clip only indexing coordinates after recording exact outside support.
        outside = (ux <= -1) | (ux >= 117) | (uy <= -1) | (uy >= 117)
        ux, uy = np.clip(ux, -1, 117), np.clip(uy, -1, 117)
        ix, iy = np.floor(ux).astype(int), np.floor(uy).astype(int)
        fx, fy = ux - ix, uy - iy
        result = np.zeros(px.shape, dtype=float)
        for dy, wy in ((0, 1 - fy), (1, fy)):
            for dx, wx in ((0, 1 - fx), (1, fx)):
                xx, yy = ix + dx, iy + dy
                valid = (xx >= 0) & (xx <= 116) & (yy >= 0) & (yy <= 116) & ~outside
                values = self.arrays[:, np.clip(yy, 0, 116), np.clip(xx, 0, 116)]
                blend = np.tensordot(weights, values, axes=(0, 0))
                result += np.where(valid, blend * wx * wy, 0.)
        return result

    def image(self, x, y, shape, corner=None):
        shape = image_shape(shape)
        weights = self.weights(x, y, corner)
        xmin, xmax = int(np.ceil(x - RADIUS)), int(np.floor(x + RADIUS))
        ymin, ymax = int(np.ceil(y - RADIUS)), int(np.floor(y + RADIUS))
        full_y, full_x = np.mgrid[ymin:ymax + 1, xmin:xmax + 1]
        full = self.sample(full_x, full_y, x, y, corner)
        normalization = float(full.sum())
        if not np.isfinite(normalization) or normalization <= 0:
            raise ValueError("STOP_FULL_SUPPORT_NORMALIZATION")
        yy, xx = np.indices(shape)
        cropped = self.sample(xx, yy, x, y, corner) / normalization
        captured = float(cropped.sum())
        if not np.all(np.isfinite(cropped)) or not np.isfinite(captured):
            raise ValueError("STOP_MODEL_NONFINITE")
        return cropped, {"full_support_normalization": normalization, "captured_fraction": captured,
                         "lost_wing_fraction": 1 - captured, "field_weights": weights.tolist(), "corner": corner,
                         "full_support_bounds_xy": [xmin, xmax, ymin, ymax],
                         "full_support_shape": list(full.shape), "normalization_domain": "finite_model_detector_lattice",
                         "true_infinite_flux": False, "negative_full_samples": int(np.count_nonzero(full < 0))}


def image_shape(shape):
    if (len(shape) != 2 or any(not isinstance(n, (int, np.integer)) or isinstance(n, bool) or not 1 <= n <= 128 for n in shape)):
        raise ValueError("STOP_IMAGE_SHAPE")
    return tuple(int(n) for n in shape)


def inputs(image, error, valid):
    data, sigma, mask = np.asarray(image, dtype=float), np.asarray(error, dtype=float), np.asarray(valid)
    shape = image_shape(data.shape)
    if sigma.shape != shape or mask.shape != shape or mask.dtype.kind != "b" or mask.sum() < 25:
        raise ValueError("STOP_FIT_INPUTS")
    if not np.all(np.isfinite(data[mask])) or not np.all(np.isfinite(sigma[mask])) or np.any(sigma[mask] <= 0):
        raise ValueError("STOP_FIT_FINITE_ERRORS")
    yy, xx = np.indices(shape, dtype=float)
    xx = (xx - (shape[1] - 1) / 2) / max(shape[1] - 1, 1)
    yy = (yy - (shape[0] - 1) / 2) / max(shape[0] - 1, 1)
    plane = np.stack([np.ones(shape), xx, yy], axis=-1)
    return data, sigma, mask, plane


def linear(data, sigma, mask, plane, model):
    design = np.column_stack([model[mask], plane[mask]])
    weighted = design / sigma[mask, None]
    coefficients, _, rank, _ = np.linalg.lstsq(weighted, data[mask] / sigma[mask], rcond=None)
    if rank != 4 or not np.all(np.isfinite(coefficients)):
        raise ValueError("STOP_LINEAR_RANK")
    prediction = coefficients[0] * model + plane @ coefficients[1:]
    residual = (prediction[mask] - data[mask]) / sigma[mask]
    if not np.all(np.isfinite(residual)):
        raise ValueError("STOP_RESIDUAL_NONFINITE")
    return coefficients, prediction, residual


def bounds(grid, shape):
    lower = np.maximum([-.5, -.5], [grid.columns[0], grid.rows[0]] - grid.origin)
    upper = np.minimum([shape[1] - .5, shape[0] - .5], [grid.columns[1], grid.rows[1]] - grid.origin)
    if np.any(lower >= upper):
        raise ValueError("STOP_FIT_BOUNDS")
    return lower, upper


def failed(error):
    return {"success": False, "status": str(error), "error_type": type(error).__name__,
            "centroid_covariance": None, "covariance_status": "NOT_AVAILABLE_FIT_FAILED",
            "localization_validated": False}


def fixed_hypothesis(image, error, valid, grid, x, y, corner=None):
    try:
        data, sigma, mask, plane = inputs(image, error, valid)
        lower, upper = bounds(grid, data.shape)
        if np.any(np.array([x, y]) < lower) or np.any(np.array([x, y]) > upper):
            raise ValueError("STOP_HYPOTHESIS_OUTSIDE_STAMP")
        model, metadata = grid.image(x, y, data.shape, corner)
        coefficients, prediction, residual = linear(data, sigma, mask, plane, model)
        score = float(residual @ residual)
        if not np.isfinite(score):
            raise ValueError("STOP_SCORE_NONFINITE")
        return {"success": True, "status": "FIXED_HYPOTHESIS_DIAGNOSTIC", "x": float(x), "y": float(y),
                "amplitude": float(coefficients[0]), "plane": coefficients[1:].tolist(),
                "weighted_residual_sum": score, "points": int(mask.sum()), "rank": 4,
                "model_metadata": metadata, "model": prediction.tolist(),
                "residual": [[float(data[r, c] - prediction[r, c]) if mask[r, c] else None
                              for c in range(data.shape[1])] for r in range(data.shape[0])], "localization_validated": False}
    except (ValueError, np.linalg.LinAlgError, FloatingPointError) as failure:
        return failed(failure)


def covariance(grid, x, y, shape, amplitude, sigma, mask, plane, lower, upper):
    model, _ = grid.image(x, y, shape)
    derivatives = []
    for axis in range(2):
        lo, hi = np.array([x, y], dtype=float), np.array([x, y], dtype=float)
        lo[axis] = max(lo[axis] - DERIVATIVE_STEP, lower[axis])
        hi[axis] = min(hi[axis] + DERIVATIVE_STEP, upper[axis])
        first, _ = grid.image(*lo, shape)
        second, _ = grid.image(*hi, shape)
        derivatives.append(amplitude * (second - first) / (hi[axis] - lo[axis]))
    jacobian = np.column_stack([model[mask], derivatives[0][mask], derivatives[1][mask], plane[mask]]) / sigma[mask, None]
    _, singular, vh = np.linalg.svd(jacobian, full_matrices=False)
    threshold = singular[0] * max(jacobian.shape) * np.finfo(float).eps
    if np.count_nonzero(singular > threshold) != 6 or singular[0] / singular[-1] > 1e12:
        return None, "STOP_COVARIANCE_RANK_OR_CONDITION"
    complete = (vh.T / singular**2) @ vh
    center = complete[1:3, 1:3]
    if not np.all(np.isfinite(center)) or np.any(np.linalg.eigvalsh(center) <= 0):
        return None, "STOP_COVARIANCE_NONPOSITIVE"
    return center.tolist(), "NOMINAL_DIAGONAL_PIXEL_ERRORS_NO_RESIDUAL_RESCALING"


def fit(image, error, valid, grid):
    evaluations = 0
    try:
        data, sigma, mask, plane = inputs(image, error, valid)
        lower, upper = bounds(grid, data.shape)
        pcoef, _, prank, _ = np.linalg.lstsq(plane[mask] / sigma[mask, None], data[mask] / sigma[mask], rcond=None)
        if prank != 3:
            raise ValueError("STOP_INITIAL_PLANE_RANK")
        initial_signal = np.where(mask, np.abs(data - plane @ pcoef), -np.inf)
        yy, xx = np.unravel_index(np.argmax(initial_signal), data.shape)
        initial = np.clip([float(xx), float(yy)], lower + 1e-8, upper - 1e-8)

        def residual(position):
            nonlocal evaluations
            evaluations += 1
            if evaluations > 4 * MAX_NFEV:
                raise ValueError("STOP_MODEL_EVALUATION_CAP")
            model, _ = grid.image(*position, data.shape)
            return linear(data, sigma, mask, plane, model)[2]

        optimized = least_squares(residual, initial, bounds=(lower, upper), max_nfev=MAX_NFEV,
                                  ftol=1e-9, xtol=1e-9, gtol=1e-9, diff_step=1e-4, method="trf")
        x, y = optimized.x
        result = fixed_hypothesis(data, sigma, mask, grid, x, y)
        if not result["success"]:
            return {**result, "evaluations": evaluations}
        hit = bool(np.any(optimized.active_mask) or np.any(optimized.x - lower <= 1e-5)
                   or np.any(upper - optimized.x <= 1e-5))
        cov, cov_status = covariance(grid, x, y, data.shape, result["amplitude"], sigma, mask, plane, lower, upper)
        result.update(success=bool(optimized.success and not hit), optimizer_success=bool(optimized.success),
                      status="FIT_DIAGNOSTIC_COMPLETE" if optimized.success and not hit else "STOP_FIT_BOUND_OR_OPTIMIZER",
                      bound_hit=hit, nfev=int(optimized.nfev), evaluations=evaluations,
                      optimizer_active_mask=np.asarray(optimized.active_mask, dtype=int).tolist(),
                      optimizer_message=str(optimized.message), initial_xy=initial.tolist(),
                      centroid_covariance=cov, covariance_status=cov_status,
                      nominal_ellipse_threshold=float(-2 * np.log(.05)))
        return result
    except (ValueError, np.linalg.LinAlgError, FloatingPointError) as failure:
        return {**failed(failure), "evaluations": evaluations}
