"""Fixed-resolution static map-support diagnostics; never an exposure verdict."""

import numpy as np

SUBDIVISIONS = (4, 8)
CHUNK_ROWS = 16
MAX_SIDE = 256
RADII = {"circle20": (0., 20.), "annulus60_90": (60., 90.)}
CATEGORIES = ("finite_positive", "zero", "negative", "nonfinite", "out_of_image")
STATUS = "STATIC_SUPPORT_APPROXIMATION_NOT_COVERAGE"


def separation(ra, dec, centre):
    ra, dec = np.deg2rad(ra), np.deg2rad(dec)
    r0, d0 = np.deg2rad(centre)
    a = np.sin((dec - d0) / 2)**2 + np.cos(dec) * np.cos(d0) * np.sin((ra - r0) / 2)**2
    return np.rad2deg(2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))) * 3600


def world(wcs, x, y):
    ra, dec = wcs.all_pix2world(x, y, 0)
    if not np.isfinite(ra).all() or not np.isfinite(dec).all():
        raise ValueError("STOP_WCS_NONFINITE")
    return ra, dec


def validate(image, wcs, centre, kind):
    if np.ma.isMaskedArray(image):
        raise ValueError("STOP_MASKED_IMAGE")
    image = np.asarray(image)
    if image.ndim != 2 or not all(0 < n <= 648 for n in image.shape) or image.dtype.kind not in "fiu":
        raise ValueError("STOP_IMAGE_SCHEMA")
    if kind not in RADII:
        raise ValueError("STOP_REGION")
    centre = np.asarray(centre, dtype=float)
    if centre.shape != (2,) or not np.isfinite(centre).all() or not (0 <= centre[0] <= 360 and -90 <= centre[1] <= 90):
        raise ValueError("STOP_CENTRE_SCHEMA")
    if (wcs.pixel_n_dim != 2 or wcs.world_n_dim != 2 or wcs.has_distortion
            or list(wcs.wcs.ctype) != ["RA---TAN", "DEC--TAN"]
            or any(str(unit) != "deg" for unit in wcs.wcs.cunit)
            or wcs.wcs.get_pv() or wcs.wcs.get_ps()):
        raise ValueError("STOP_WCS_SCHEMA")
    matrix = np.asarray(wcs.pixel_scale_matrix, dtype=float)
    if matrix.shape != (2, 2) or not np.isfinite(matrix).all():
        raise ValueError("STOP_WCS_MATRIX")
    singular = np.linalg.svd(matrix, compute_uv=False)
    if singular[-1] <= 0:
        raise ValueError("STOP_WCS_SINGULAR")
    inner, outer = RADII[kind]
    theta = float(separation(*centre, wcs.wcs.crval) / 3600) + outer / 3600
    if theta >= 2:
        raise ValueError("STOP_TAN_RADIUS")
    cx, cy = wcs.all_world2pix(*centre, 0)
    if not np.isfinite([cx, cy]).all():
        raise ValueError("STOP_WCS_NONFINITE")
    # The gnomonic differential has maximum stretch sec(theta)^2. The
    # inverse linear pixel transform contributes 1/sigma_min, in degrees.
    radius = outer / 3600 / singular[-1] / np.cos(np.deg2rad(theta))**2
    half = int(np.ceil(radius)) + 2
    bounds = (int(np.floor(cx)) - half, int(np.ceil(cx)) + half,
              int(np.floor(cy)) - half, int(np.ceil(cy)) + half)
    if bounds[1] - bounds[0] + 1 > MAX_SIDE or bounds[3] - bounds[2] + 1 > MAX_SIDE:
        raise ValueError("STOP_REGION_BOX_CAP")
    x = np.array([cx, bounds[0], bounds[0], bounds[1], bounds[1]])
    y = np.array([cy, bounds[2], bounds[3], bounds[2], bounds[3]])
    ra, dec = world(wcs, x, y)
    rx, ry = wcs.all_world2pix(ra, dec, 0)
    if not np.isfinite([rx, ry]).all() or np.max(np.hypot(rx - x, ry - y)) > 1e-6:
        raise ValueError("STOP_WCS_ROUNDTRIP")
    return image, centre, (inner, outer), bounds, abs(float(np.linalg.det(matrix))) * 3600**2


def categories(image, x, y):
    inside = (x >= 0) & (x < image.shape[1]) & (y >= 0) & (y < image.shape[0])
    values = np.zeros(x.shape, dtype=float)
    values[inside] = image[y[inside], x[inside]]
    return {"finite_positive": inside & np.isfinite(values) & (values > 0),
            "zero": inside & (values == 0), "negative": inside & np.isfinite(values) & (values < 0),
            "nonfinite": inside & ~np.isfinite(values), "out_of_image": ~inside}


def raster(image, wcs, centre, radii, bounds, pixel_area, subdivision):
    xmin, xmax, ymin, ymax = bounds
    counts = {key: 0 for key in CATEGORIES}
    base_counts = {key: 0 for key in CATEGORIES}
    areas = {key: 0. for key in CATEGORIES}
    offsets = (np.arange(subdivision) + .5) / subdivision - .5
    for start in range(ymin, ymax + 1, CHUNK_ROWS):
        x, y = np.meshgrid(np.arange(xmin, xmax + 1), np.arange(start, min(start + CHUNK_ROWS, ymax + 1)))
        code = categories(image, x, y)
        touched = {key: np.zeros(x.shape, dtype=bool) for key in CATEGORIES}
        for dy in offsets:
            for dx in offsets:
                ra, dec = world(wcs, x + dx, y + dy)
                distance = separation(ra, dec, centre)
                selected = (distance >= radii[0]) & (distance < radii[1])
                # Midpoint solid-angle Jacobian of TAN, not exact spherical
                # pixel-polygon integration; report both fixed resolutions.
                theta = np.deg2rad(separation(ra, dec, wcs.wcs.crval) / 3600)
                area = pixel_area * np.cos(theta)**3 / subdivision**2
                for key in CATEGORIES:
                    chosen = selected & code[key]
                    counts[key] += int(chosen.sum())
                    areas[key] += float(area[chosen].sum())
                    touched[key] |= chosen
        for key in CATEGORIES:
            base_counts[key] += int(touched[key].sum())
    total = sum(areas.values())
    return {"subdivision": subdivision, "selected_subpixel_counts": counts,
            "sampled_intersected_base_pixel_counts": base_counts, "estimated_area_arcsec2": areas,
            "estimated_total_area_arcsec2": total,
            "estimated_area_fractions": {k: areas[k] / total if total > 0 else None for k in CATEGORIES}}


def proximity(image, wcs, centre, outer):
    nearest, unsupported = None, 0
    ny, nx = image.shape
    for start in range(0, ny, CHUNK_ROWS):
        x, y = np.meshgrid(np.arange(nx), np.arange(start, min(start + CHUNK_ROWS, ny)))
        values = image[y, x]
        bad = ~np.isfinite(values) | (values <= 0)
        unsupported += int(bad.sum())
        if bad.any():
            ra, dec = world(wcs, x[bad], y[bad])
            value = float(separation(ra, dec, centre).min())
            nearest = value if nearest is None else min(nearest, value)
    # Pixel-boundary rectangle sampled every one pixel, including all corners.
    xs, ys = np.arange(nx + 1) - .5, np.arange(ny + 1) - .5
    bx = np.concatenate((xs, xs, np.full(ny + 1, -.5), np.full(ny + 1, nx - .5)))
    by = np.concatenate((np.full(nx + 1, -.5), np.full(nx + 1, ny - .5), ys, ys))
    ra, dec = world(wcs, bx, by)
    border = float(separation(ra, dec, centre).min())
    cx, cy = wcs.all_world2pix(*centre, 0)
    return {"unsupported_image_pixel_count": unsupported,
            "nearest_unsupported_pixel_centre_arcsec": nearest,
            "unsupported_pixel_centre_minus_outer_radius_arcsec": None if nearest is None else nearest - outer,
            "nearest_sampled_image_border_arcsec": border,
            "sampled_image_border_minus_outer_radius_arcsec": border - outer,
            "region_centre_inside_image_rectangle": bool(-.5 <= cx <= nx - .5 and -.5 <= cy <= ny - .5),
            "border_sample_spacing_pixels": 1,
            "interpretation": "Distances to pixel centres / sampled border, not true nearest-boundary guarantees or eligibility"}


def summarize(image, wcs, centre, kind):
    """One caller-fixed region, never select/move a centre using the data.

    Coordinates remain input-only. Positive values mean accumulated support;
    their amplitude does not weight geometric area or supply live exposure.
    """
    image, centre, radii, bounds, pixel_area = validate(image, wcs, centre, kind)
    estimates = [raster(image, wcs, centre, radii, bounds, pixel_area, n) for n in SUBDIVISIONS]
    inner, outer = np.deg2rad(np.array(radii) / 3600)
    exact_area = float(4 * np.pi * (np.sin(outer / 2)**2 - np.sin(inner / 2)**2) * (180 * 3600 / np.pi)**2)
    return {"status": STATUS, "region": kind, "radii_arcsec": list(radii), "nominal_subdivision": 8,
            "analytical_full_spherical_region_area_arcsec2": exact_area, "resolutions": estimates,
            "fine_minus_coarse_area_arcsec2": {k: estimates[1]["estimated_area_arcsec2"][k] - estimates[0]["estimated_area_arcsec2"][k]
                                               for k in CATEGORIES},
            "fine_minus_analytical_full_area_arcsec2": estimates[1]["estimated_total_area_arcsec2"] - exact_area,
            "proximity": proximity(image, wcs, centre, radii[1]),
            "interpretation": "Fixed midpoint raster / TAN Jacobian approximations, not exact area, matched FLAG masks, live exposure or continuous coverage"}
