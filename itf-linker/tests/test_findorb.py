"""Parsers for Find_Orb output, pinned against captured real ``fo`` runs.

Fixtures in ``tests/data/fo/`` were produced by the build documented in DATA-SOURCES.md,
fitting real ITF designations. No WSL, no Find_Orb, and no network are needed to run these.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import pytest

from itf_linker.fit.findorb import (
    FO_OUTPUT_FILES,
    FitResult,
    max_residual,
    parse_covar_json,
    parse_elements_txt,
    parse_total_json,
    rms_from_residuals,
)
from itf_linker.fit.gates import (
    MAX_RMS_ARCSEC,
    THREE_NIGHT_SIGMA_A_AU,
    post_fit_gate,
)
from itf_linker.fit.wsl import Shell, from_wsl_path, shq, shq_expand, to_wsl_path

FO = Path(__file__).parent / "data" / "fo"

#: The two designations the fixtures were captured from.
GOOD = "RL00adt"
BAD = "/12S010"


def _read(name: str) -> str:
    return (FO / name).read_text(encoding="utf-8", errors="replace")


# ----------------------------------------------------------------------------------
# total.json
# ----------------------------------------------------------------------------------

def test_parses_a_converged_solution():
    fits = parse_total_json(_read("converged_total.json"), requested=[GOOD])
    assert set(fits) == {GOOD}
    fit = fits[GOOD]
    assert fit.converged and fit.status == "converged"
    # Every quantity the MPC's published criteria consume must be present.
    for attr in ("rms_residual", "sigma_a", "sigma_q", "sigma_i", "sigma_e"):
        assert getattr(fit, attr) is not None, attr
    assert fit.a > 0 and 0 <= fit.e < 1
    assert fit.q == pytest.approx(fit.a * (1 - fit.e), rel=1e-6)
    assert fit.n_used == fit.n_obs
    assert fit.central_body == "Sun" and fit.frame == "J2000 ecliptic"


def test_reported_rms_matches_the_residual_table():
    """An independent recomputation from the per-observation residuals.

    A parser that latched onto the wrong JSON field would sail through every other test
    here; it cannot survive agreeing with a number derived a different way.
    """
    fit = parse_total_json(_read("converged_total.json"), requested=[GOOD])[GOOD]
    assert rms_from_residuals(fit.residuals) == pytest.approx(fit.rms_residual, rel=0.02)


def test_max_residual_ignores_excluded_observations():
    """Inclusion is the ``incl`` field, not ``flags`` -- ``flags`` stays 0 when rejected."""
    residuals = [
        {"dRA": 0.1, "dDec": 0.0, "incl": 1, "flags": 0},
        {"dRA": 900.0, "dDec": 0.0, "incl": 0, "flags": 0},
    ]
    assert max_residual(residuals) == pytest.approx(0.1)
    # Per-coordinate normalisation: one used observation contributes two residuals,
    # so sqrt((0.1^2 + 0^2) / 2), not sqrt(0.1^2 / 1).
    assert rms_from_residuals(residuals) == pytest.approx(0.1 / math.sqrt(2))


def test_non_convergence_is_detected_by_absent_sigmas():
    fits = parse_total_json(_read("no_covariance_total.json"), requested=[BAD])
    fit = fits[BAD]
    assert not fit.converged
    assert fit.status == "no_covariance"
    # Find_Orb still emitted a preliminary orbit -- which is exactly the trap.
    assert fit.a is not None
    assert fit.sigma_a is None
    assert fit.rms_residual is not None


def test_multi_object_run_keys_every_object():
    fits = parse_total_json(_read("pair_total.json"), requested=[GOOD, BAD])
    assert set(fits) == {GOOD, BAD}
    assert fits[GOOD].converged
    assert not fits[BAD].converged


def test_designation_recovered_from_the_packed_field():
    """Find_Orb renames what it recognises; the trkSub lives in columns 6-12 of ``packed``."""
    doc = {
        "num": 1,
        "ids": ["Jupiter IX = Sinope"],
        "objects": {
            "Jupiter IX = Sinope": {
                "object": "Jupiter IX = Sinope",
                "packed": "     J009S  ",
                "elements": {"q": 5.0, "a": 5.2, "e": 0.1, "rms_residual": 0.3},
                "observations": {"count": 3, "used": 3, "residuals": []},
            }
        },
    }
    fits = parse_total_json(json.dumps(doc), requested=["J009S"])
    assert "J009S" in fits
    assert fits["J009S"].fo_object_name == "Jupiter IX = Sinope"


def test_unrequested_object_keeps_its_own_name():
    doc = {
        "objects": {
            "73P-C": {
                "object": "73P-C",
                "packed": "0073P     C ",
                "elements": {"q": 0.9, "a": 3.1, "e": 0.7, "rms_residual": 0.2},
                "observations": {"count": 5, "used": 5, "residuals": []},
            }
        }
    }
    assert "73P-C" in parse_total_json(json.dumps(doc), requested=["nope"])


def test_unbound_orbit_is_not_reported_as_converged():
    doc = {
        "objects": {
            "X": {
                "object": "X",
                "packed": "     X      ",
                "elements": {
                    "q": 1.0, "a": -3.0, "e": 1.4, "i": 12.0, "rms_residual": 0.1,
                    "a sigma": 0.01, "q sigma": 0.01, "i sigma": 0.01, "e sigma": 0.01,
                },
                "observations": {"count": 6, "used": 6, "residuals": []},
            }
        }
    }
    fit = parse_total_json(json.dumps(doc), requested=["X"])["X"]
    assert not fit.converged and fit.status == "unbound"


def test_non_finite_values_become_none():
    doc = {
        "objects": {
            "X": {
                "object": "X", "packed": "     X      ",
                "elements": {"q": 1.0, "a": float("nan"), "e": 0.1, "rms_residual": 0.1},
                "observations": {"count": 3, "used": 3, "residuals": []},
            }
        }
    }
    fit = parse_total_json(json.dumps(doc), requested=["X"])["X"]
    assert fit.a is None and not fit.converged


# ----------------------------------------------------------------------------------
# covar.json and elements.txt
# ----------------------------------------------------------------------------------

def test_covariance_is_square_symmetric_and_positive_diagonal():
    cov = parse_covar_json(_read("converged_covar.json"))
    matrix = cov["covariance"]
    assert len(matrix) == 6 and all(len(row) == 6 for row in matrix)
    assert len(cov["state_vector"]) == 6
    assert cov["epoch_jd"] > 2_400_000
    for i in range(6):
        assert matrix[i][i] > 0
        for j in range(6):
            assert matrix[i][j] == pytest.approx(matrix[j][i], rel=1e-9)


def test_force_model_is_recovered_from_elements_txt():
    model = parse_elements_txt(_read("converged_elements.txt"))
    assert model["perturbers"] == "000007fe"
    assert "Merc-Pluto" in model["perturbers_label"]
    assert "DE-440" in model["jpl_ephemeris"]


def test_unperturbed_run_is_distinguishable():
    """Find_Orb's shipped default is PERTURBERS=0, which is wrong for a 7-day MBA arc."""
    model = parse_elements_txt(_read("unperturbed_elements.txt"))
    assert model["perturbers"] == "00000000"
    assert model["perturbers_label"] == "unperturbed orbit"


def test_elements_txt_without_a_perturber_line_returns_empty():
    assert parse_elements_txt("Orbital elements: nothing useful here\n") == {}


# ----------------------------------------------------------------------------------
# The published post-fit gate
# ----------------------------------------------------------------------------------

def _fit(**kw) -> FitResult:
    base = {
        "desig": "T", "converged": True, "status": "converged", "rms_residual": 0.1,
        "sigma_a": 0.01, "sigma_q": 0.01, "sigma_i": 0.1, "sigma_e": 0.01,
        "n_obs": 9, "n_used": 9, "a": 2.5, "e": 0.1, "q": 2.25,
    }
    return FitResult(**{**base, **kw})


def test_gate_accepts_a_good_three_night_fit():
    assert post_fit_gate(_fit(), n_nights=3).passes


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"rms_residual": MAX_RMS_ARCSEC + 0.001}, "RMS"),
        ({"converged": False, "status": "no_covariance"}, "non-convergence"),
        ({"sigma_a": THREE_NIGHT_SIGMA_A_AU}, "sigma(a)"),
        ({"sigma_q": 0.06}, "sigma(q)"),
        ({"sigma_i": 0.5}, "sigma(i)"),
        ({"sigma_e": 0.05}, "sigma(e)"),
        ({"sigma_a": None}, "sigma(a)"),
    ],
)
def test_gate_rejects_each_published_failure_mode(kwargs, fragment):
    """Each criterion is verified to reject on its own, so passing is never vacuous."""
    result = post_fit_gate(_fit(**kwargs), n_nights=3)
    assert not result.passes
    assert any(fragment in r for r in result.reasons), result.reasons


def test_sigma_limits_apply_only_to_three_night_links():
    """The MPC imposes them on 3-night links; a 4-night link is judged on RMS alone."""
    loose = _fit(sigma_a=784.0, sigma_q=9.0, sigma_i=90.0, sigma_e=0.9)
    assert not post_fit_gate(loose, n_nights=3).passes
    assert post_fit_gate(loose, n_nights=4).passes
    assert post_fit_gate(loose, n_nights=4).tight_sigmas_required is False


def test_rms_exactly_at_the_limit_is_accepted():
    assert post_fit_gate(_fit(rms_residual=MAX_RMS_ARCSEC), n_nights=3).passes


# ----------------------------------------------------------------------------------
# The WSL bridge
# ----------------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("windows", "wsl"),
    [
        (r"C:\Users\me\itf", "/mnt/c/Users/me/itf"),
        (r"D:\a\b\c.txt", "/mnt/d/a/b/c.txt"),
        (r"c:/lower/case", "/mnt/c/lower/case"),
        ("/home/me/itf", "/home/me/itf"),
        ("relative/path", "relative/path"),
    ],
)
def test_path_translation(windows, wsl):
    assert to_wsl_path(windows) == wsl


def test_path_translation_round_trips():
    assert from_wsl_path(to_wsl_path(r"C:\Users\me\itf")) == r"C:\Users\me\itf"
    assert from_wsl_path("/home/me/x") == "/home/me/x"


def test_shell_path_makes_relative_paths_absolute():
    """A relative -O would resolve against fo's own working directory and lose the output."""
    shell = Shell(use_wsl=True)
    out = shell.path("data/fits/chunk0000")
    # Absoluteness is the invariant that matters -- it is what stops ``fo`` writing to
    # <workdir>/<workdir>. The ``/mnt/`` prefix is merely what that looks like when a
    # Windows drive path is translated, so assert it only where translation happens.
    assert out.startswith("/")
    assert out.endswith("data/fits/chunk0000")
    if os.name == "nt":
        assert out.startswith("/mnt/")


def test_quoting_distinguishes_data_from_configuration():
    # Data is quoted so nothing expands...
    assert shq("$HOME/a b") == "'$HOME/a b'"
    assert shq("it's") == "'it'\\''s'"
    # ...configuration is quoted so $HOME still does.
    assert shq_expand("$HOME/bin/fo") == '"$HOME/bin/fo"'
    assert shq_expand('a"b') == '"a\\"b"'


def test_output_files_are_never_symlinked_into_a_worker_config():
    """The shared-elements.json trap: these are fo's outputs, not its data."""
    for name in ("elements.json", "total.json", "covar.json", "elem_short.json"):
        assert name in FO_OUTPUT_FILES
    assert "cospar.txt" not in FO_OUTPUT_FILES
    assert "ObsCodes.htm" not in FO_OUTPUT_FILES


def test_shell_selects_wsl_only_where_it_is_needed():
    assert Shell(use_wsl=True).argv("x")[0] == "wsl.exe"
    assert Shell(use_wsl=False).argv("x")[0] == "bash"


def test_fit_result_arc_days():
    fit = FitResult(desig="T", first_jd=2460000.5, last_jd=2460007.5)
    assert fit.arc_days == pytest.approx(7.0)
    assert FitResult(desig="T").arc_days is None
    assert not math.isnan(fit.arc_days)


# ----------------------------------------------------------------------------------
# Resuming an interrupted batch
# ----------------------------------------------------------------------------------

def test_resume_reads_back_a_completed_chunk(tmp_path):
    """A finished chunk directory must reconstruct without re-running ``fo``.

    Fitting an M3 batch is hours of ``fo``; an interrupted run that had to start over
    would make the milestone unfinishable on a laptop. The force model has to come back
    with it, because it is parsed from ``elements.txt``, not from ``total.json``.
    """
    from itf_linker.fit.findorb import load_previous_run

    (tmp_path / "total.json").write_text(_read("pair_total.json"), encoding="utf-8")
    (tmp_path / "elements.txt").write_text(_read("converged_elements.txt"), encoding="utf-8")
    results = load_previous_run(tmp_path, [GOOD, BAD])
    assert results is not None
    assert set(results) == {GOOD, BAD}
    assert results[GOOD].converged
    assert results[GOOD].perturbers == "000007fe"


def test_resume_refuses_a_chunk_that_is_missing_a_designation(tmp_path):
    """Half a chunk is worse than none: it turns "not fitted" into "did not converge"."""
    from itf_linker.fit.findorb import load_previous_run

    (tmp_path / "total.json").write_text(_read("converged_total.json"), encoding="utf-8")
    assert load_previous_run(tmp_path, [GOOD, BAD]) is None
    assert load_previous_run(tmp_path, [GOOD]) is not None


def test_resume_refuses_a_truncated_file(tmp_path):
    from itf_linker.fit.findorb import load_previous_run

    (tmp_path / "total.json").write_text(_read("converged_total.json")[:200], encoding="utf-8")
    assert load_previous_run(tmp_path, [GOOD]) is None
    assert load_previous_run(tmp_path / "nowhere", [GOOD]) is None
