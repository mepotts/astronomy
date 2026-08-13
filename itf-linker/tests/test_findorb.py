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
    MAX_ECCENTRICITY,
    MAX_RMS_ARCSEC,
    QUALITY_SIGMA_A_AU,
    mpc_published_gate,
    orbit_quality_sufficient,
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
# Our post-fit gate (strict), and the MPC's published one
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
        ({"sigma_a": QUALITY_SIGMA_A_AU}, "sigma(a)"),
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


def test_our_gate_scopes_the_sigmas_to_three_night_links():
    """*Our* scoping, not the MPC's -- their bullet 2 governs >3-night links too.

    Pinned because M1-M5 pass rates are all against this behaviour; the naming used to
    claim the MPC imposed the scoping, which :func:`mpc_published_gate` shows it does not.
    """
    loose = _fit(sigma_a=784.0, sigma_q=9.0, sigma_i=90.0, sigma_e=0.9)
    assert not post_fit_gate(loose, n_nights=3).passes
    assert post_fit_gate(loose, n_nights=4).passes
    assert post_fit_gate(loose, n_nights=4).tight_sigmas_required is False


def test_rms_exactly_at_the_limit_is_accepted():
    assert post_fit_gate(_fit(rms_residual=MAX_RMS_ARCSEC), n_nights=3).passes


def test_an_rms_of_exactly_zero_passes_the_ceiling_rather_than_being_falsy():
    """Six elements fitted to three observations give RMS identically 0.0, not a rounding
    artefact. `(rms or 9e9)` treated that as failing; the counters used to disagree with the
    gate by one record. The subset guard is what should reject these, on used-observations.
    """
    assert post_fit_gate(_fit(rms_residual=0.0), n_nights=3).passes
    assert not post_fit_gate(_fit(rms_residual=None), n_nights=3).passes


def test_our_gate_ignores_eccentricity_and_the_published_one_does_not():
    """``e < 0.5`` is published; our frozen gate never applied it. Both facts pinned."""
    hyperbolic = _fit(e=0.984, rms_residual=0.9, sigma_a=9.0)
    assert post_fit_gate(hyperbolic, n_nights=4).passes is False  # rejected on RMS, not e
    assert post_fit_gate(_fit(e=0.984), n_nights=4).passes  # good RMS -> our gate lets it by
    assert not orbit_quality_sufficient(_fit(e=MAX_ECCENTRICITY))
    assert orbit_quality_sufficient(_fit(e=0.49))


# --- the MPC's published rule: conjunctive, so RMS alone never rejects ---------------

def test_published_gate_does_not_reject_on_rms_alone():
    """The conjunct our gate applies unconditionally. 36,192 M5 fits turn on this."""
    noisy_but_well_constrained = _fit(rms_residual=3.0)
    assert not post_fit_gate(noisy_but_well_constrained, n_nights=4).passes
    assert mpc_published_gate(noisy_but_well_constrained, n_nights=4, arc_days=6.0).passes


def test_published_gate_rejects_only_when_every_conjunct_holds():
    bad_quality = {"sigma_a": 9.0, "sigma_q": 9.0, "sigma_i": 90.0, "sigma_e": 0.9}
    doomed = _fit(rms_residual=3.0, **bad_quality)
    #  3 nights, arc < 15 d, RMS > 0.25", quality insufficient -> all four conjuncts
    assert not mpc_published_gate(doomed, n_nights=3, arc_days=6.0).passes
    #  break any single conjunct and it survives
    assert mpc_published_gate(doomed, n_nights=3, arc_days=20.0).passes      # arc too long
    assert mpc_published_gate(_fit(**bad_quality), n_nights=3, arc_days=6.0).passes  # RMS ok
    assert mpc_published_gate(_fit(rms_residual=3.0), n_nights=3, arc_days=6.0).passes  # quality ok


def test_published_gate_uses_the_ten_day_ceiling_above_three_nights():
    """Bullet 2 exists: >3 nights is governed, not exempt -- the A3 misreading."""
    doomed = _fit(rms_residual=3.0, sigma_a=9.0, sigma_q=9.0, sigma_i=90.0, sigma_e=0.9)
    assert not mpc_published_gate(doomed, n_nights=5, arc_days=6.0).passes
    assert mpc_published_gate(doomed, n_nights=5, arc_days=12.0).passes   # 12 d > 10 d
    assert not mpc_published_gate(doomed, n_nights=3, arc_days=12.0).passes  # but < 15 d


def test_published_gate_rejects_non_convergence_regardless():
    assert not mpc_published_gate(
        _fit(converged=False, status="no_covariance"), n_nights=4, arc_days=6.0
    ).passes


def test_published_gate_counts_high_eccentricity_as_insufficient_quality():
    doomed = _fit(rms_residual=3.0, e=0.984)
    result = mpc_published_gate(doomed, n_nights=3, arc_days=6.0)
    assert not result.passes
    assert any("e 0.984" in r for r in result.reasons), result.reasons


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


def test_completed_only_reports_finished_chunks_and_runs_nothing(tmp_path):
    """An unfinishable fit is still worth reporting as far as it got.

    ``fo`` must not be invoked at all here -- there is no shell, so any attempt to run it
    would raise rather than quietly return nothing.
    """
    from itf_linker.fit.findorb import run_fo_batched

    chunk = tmp_path / "chunk0000"
    chunk.mkdir()
    (chunk / "total.json").write_text(_read("pair_total.json"), encoding="utf-8")
    (chunk / "elements.txt").write_text(_read("converged_elements.txt"), encoding="utf-8")

    class _NoShell:
        fo_path = "/nonexistent/fo"
        config_dir = "/nonexistent/.find_orb"

        def available(self):
            return False

        def run(self, *a, **k):  # pragma: no cover - must never be reached
            raise AssertionError("fo was invoked under completed_only")

    groups = {GOOD: ["x"], BAD: ["y"], "lnkzzzz": ["z"]}
    out = run_fo_batched(
        groups, tmp_path, shell=_NoShell(), workers=1, chunk_size=2,
        resume=True, completed_only=True,
    )
    assert set(out) == {GOOD, BAD}          # the finished chunk
    assert "lnkzzzz" not in out             # the chunk nobody ran


# --- the Linux-side scratch directory -----------------------------------------------
#
# On Windows the chunk directory lives on /mnt/c, which `fo` reaches over WSL's 9p bridge:
# no page cache, and every concurrent worker serialised behind it. Running in a Linux
# scratch directory and copying back the three files this module reads is worth about 9x
# under load. What must never change is the answer, so these tests pin the command rather
# than the timing: same binary, same input file, same -x config, same -O target as the
# directory it runs in, and total.json copied back without a `|| true` that could hide its
# absence.

class _RecordingShell:
    """A Shell that records the script instead of running it."""

    fo_path = "$HOME/bin/fo"
    config_dir = "$HOME/.find_orb"

    def __init__(self):
        self.scripts = []

    def path(self, p):
        return "/mnt/c/work/chunk0000"

    def run(self, script, **_k):
        import subprocess

        self.scripts.append(script)
        return subprocess.CompletedProcess([], 0, "", "")


def test_scratch_run_copies_total_json_back_and_cleans_up(tmp_path):
    from itf_linker.fit.findorb import SCRATCH_OUTPUTS, run_fo

    shell = _RecordingShell()
    run_fo(["obs line"], tmp_path, designations=["lnk0000"], shell=shell,
           config_dir="/cfg/", scratch_dir="$HOME/.cache/w/chunk0000")
    script = shell.scripts[0]
    assert "mkdir -p" in script
    assert "/obs.txt" in script                              # input copied in
    for name in SCRATCH_OUTPUTS:
        assert name in script                                # outputs copied back
    # total.json's copy is unguarded: a silent failure there would be read as "fo produced
    # nothing" and bisected into forty single-object runs.
    assert 'cp "$HOME/.cache/w/chunk0000"/total.json' in script
    assert "total.json '/mnt/c/work/chunk0000/' 2>/dev/null" not in script
    assert "rm -rf" in script


def test_a_failed_copy_back_does_not_exit_with_fo_s_return_code(tmp_path):
    """The script used to end `exit $rc` with `$rc` captured *before* the copy ran.

    So `fo` succeeding and the copy-back failing exited 0, and the chunk was diagnosed as an
    `fo` abort and bisected forty ways. Both outcomes must now be distinguishable from the
    exit code alone: `fo`'s own failure still wins, a copy failure after a good run reports
    COPY_BACK_FAILED.
    """
    from itf_linker.fit.findorb import COPY_BACK_FAILED, run_fo

    shell = _RecordingShell()
    run_fo(["obs line"], tmp_path, designations=["lnk0000"], shell=shell,
           config_dir="/cfg/", scratch_dir="$HOME/.cache/w/chunk0000")
    script = shell.scripts[0].rstrip()

    assert not script.endswith("exit $rc"), "fo's code must not be the last word"
    assert "cprc=$?" in script                                  # the copy's status is kept
    assert "if [ $rc -ne 0 ]; then exit $rc; fi" in script       # a crashed fo still wins
    assert f"if [ $cprc -ne 0 ]; then exit {COPY_BACK_FAILED}; fi" in script
    assert script.endswith("exit 0")
    # and the scratch directory is still removed on every path
    assert "rm -rf" in script.split("cprc=$?")[1]


def test_scratch_and_direct_runs_pass_fo_the_same_arguments(tmp_path):
    """The only difference between the two paths must be *where*, never *what*."""
    from itf_linker.fit.findorb import run_fo

    direct, scratched = _RecordingShell(), _RecordingShell()
    run_fo(["l"], tmp_path, designations=["d"], shell=direct, config_dir="/cfg/")
    run_fo(["l"], tmp_path, designations=["d"], shell=scratched, config_dir="/cfg/",
           scratch_dir="/scratch/c0")

    def fo_call(script):
        start = script.index("$HOME/bin/fo")
        return script[start:].split(";")[0].strip()

    a, b = fo_call(direct.scripts[0]), fo_call(scratched.scripts[0])
    assert a.split(" -O ")[0] == b.split(" -O ")[0]           # same binary, same obs.txt
    assert a.split(" -x ")[1] == b.split(" -x ")[1]           # same config, flags, -q -i
    assert " -O '/mnt/c/work/chunk0000'" in a
    assert ' -O "/scratch/c0"' in b                           # -O follows the working dir


def test_obs_txt_is_written_to_the_host_even_when_fo_runs_elsewhere(tmp_path):
    """The astrometry that went in stays next to the results, scratch or not."""
    from itf_linker.fit.findorb import run_fo

    run_fo(["a line", "b line"], tmp_path, designations=["d"], shell=_RecordingShell(),
           config_dir="/cfg/", scratch_dir="/scratch/c0")
    assert (tmp_path / "obs.txt").read_text(encoding="ascii").splitlines() == ["a line", "b line"]
