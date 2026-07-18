/**
 * App entry (M1 — the Hellings–Downs Live Demo).
 *
 * Wires three views together around a single piece of state: the selected angular
 * separation θ (degrees, 0–180).
 *
 *   • SkyMap        — click two pulsars → θ = angular separation between them.
 *   • θ slider      — set an arbitrary θ directly.
 *   • HDCurvePlot   — a marker rides the analytic curve at θ; drag it to set θ.
 *
 * θ is owned HERE. Each view either reports a desired θ (slider/curve drag/pair pick) or
 * is told the current θ (`syncViews`). This one-way flow keeps all three in sync without
 * circular updates. Selecting a pair also fills in θ; conversely, moving the slider or
 * dragging the marker clears the explicit pair (an arbitrary θ has no single pulsar pair).
 */
import { renderHDCurvePlot, type HDCurveController } from "./components/HDCurvePlot";
import { renderSkyMap, type SkyMapController } from "./components/SkyMap";
import { renderResidualPanel } from "./components/ResidualPanel";
import { attachAnnotations, type Annotation } from "./components/annotations";
import { angularSeparationBetween } from "./physics/angularSeparation";
import { hellingsDownsDeg } from "./physics/hellingsDowns";
import { SECONDS_PER_YEAR, type SourceParams } from "./physics/residuals";
import { pulsars, isPlaceholderData, type Pulsar } from "./data/pulsars";
import { hdBackdropPoints, hasBackdropPoints } from "./data/hdPoints";

const DEG2RAD = Math.PI / 180;

const ATTRIBUTION =
  "Pulsar positions derived from the NANOGrav 15-year Data Set " +
  "(Agazie et al. 2023, ApJL 951 L9; data: Zenodo 10.5281/zenodo.7967584), used under " +
  "CC-BY-4.0. Hellings–Downs reference points digitized from Agazie et al. 2023, " +
  "ApJL 951 L8 (arXiv:2306.16213), shown for illustration. This is an independent " +
  "educational tool, not affiliated with or endorsed by NANOGrav.";

// ---------------------------------------------------------------------------
// State (single source of truth)
// ---------------------------------------------------------------------------
let theta = 0; // degrees, 0..180
let selectedPair: [Pulsar, Pulsar] | null = null;

// ---------------------------------------------------------------------------
// DOM handles
// ---------------------------------------------------------------------------
const slider = document.getElementById("theta-slider") as HTMLInputElement | null;
const thetaReadout = document.getElementById("theta-readout");
const pairStatus = document.getElementById("pair-status");
const randomBtn = document.getElementById("random-pair") as HTMLButtonElement | null;
const skymapEl = document.getElementById("skymap");
const plotEl = document.getElementById("plot");
const banner = document.getElementById("data-banner");
const backdropNote = document.getElementById("backdrop-note");
const footer = document.getElementById("site-footer");

let curve: HDCurveController | null = null;
let skymap: SkyMapController | null = null;

// ---------------------------------------------------------------------------
// View sync
// ---------------------------------------------------------------------------
const clampTheta = (t: number) => (t < 0 ? 0 : t > 180 ? 180 : t);

/** Push the current θ + pair-status text into the slider, readout, and curve marker. */
function syncViews() {
  if (slider) slider.value = String(theta);
  if (thetaReadout) thetaReadout.textContent = `${theta.toFixed(1)}°`;
  curve?.update(theta);

  if (pairStatus) {
    if (selectedPair) {
      const [a, b] = selectedPair;
      const corr = hellingsDownsDeg(theta);
      pairStatus.textContent =
        `${a.name} ↔ ${b.name}: separated by ${theta.toFixed(1)}° on the sky ` +
        `→ expected correlation Γ = ${corr.toFixed(3)}.`;
    } else {
      pairStatus.textContent =
        "No pulsar pair selected — showing an arbitrary angle. " +
        "Pick two dots above to use a real pair.";
    }
  }
}

// Re-entrancy guard: clearing the map's highlight calls back into setPair, and we don't
// want that nested call to double-paint. The outer call does the single syncViews().
let suppressSync = false;

/** Set θ from the slider or a marker drag: this means "arbitrary θ", so clear the pair. */
function setThetaFromControl(next: number) {
  theta = clampTheta(next);
  if (selectedPair) {
    selectedPair = null;
    suppressSync = true;
    skymap?.setPair(null, null); // clears the map highlight; nested sync suppressed
    suppressSync = false;
  }
  syncViews();
}

/** Set θ from a selected pulsar pair (θ is derived from their on-sky separation). */
function setPair(a: Pulsar | null, b: Pulsar | null) {
  if (a && b) {
    selectedPair = [a, b];
    theta = clampTheta(angularSeparationBetween(a, b));
  } else {
    selectedPair = null;
    // keep θ as-is when only a partial selection exists
  }
  if (!suppressSync) syncViews();
}

// ---------------------------------------------------------------------------
// Build the UI
// ---------------------------------------------------------------------------
if (skymapEl) {
  skymap = renderSkyMap(skymapEl, pulsars, {
    onPairSelected: (a, b) => setPair(a, b),
  });
}

if (plotEl) {
  curve = renderHDCurvePlot(plotEl, {
    backdropPoints: hasBackdropPoints ? hdBackdropPoints : undefined,
    initialThetaDeg: theta,
    onThetaChange: (t) => setThetaFromControl(t),
  });
}

if (slider) {
  slider.addEventListener("input", () => {
    setThetaFromControl(parseFloat(slider.value));
  });
}

if (randomBtn) {
  randomBtn.addEventListener("click", () => {
    if (pulsars.length < 2) return;
    let i = Math.floor(Math.random() * pulsars.length);
    let j = Math.floor(Math.random() * pulsars.length);
    while (j === i) j = Math.floor(Math.random() * pulsars.length);
    // route through the sky map so its highlight + connector update too
    skymap?.setPair(pulsars[i], pulsars[j]);
  });
}

// Placeholder-data banner (honest about non-real positions in M0/fallback).
if (banner && isPlaceholderData) {
  banner.className = "banner banner-warn";
  banner.innerHTML =
    `<strong>Placeholder data:</strong> showing ${pulsars.length} well-known pulsars, ` +
    "not yet the full 67-pulsar NANOGrav 15-year array. The positions shown are real, " +
    "but the set is incomplete. Run <code>scripts/build-pulsars.mjs</code> on the Zenodo " +
    "<code>.par</code> files to populate all 67 (see DATA-SOURCES.md §2).";
}

// Backdrop note (illustrative label, or a note that none are loaded yet).
if (backdropNote) {
  backdropNote.innerHTML = hasBackdropPoints
    ? `Blue points: ${hdBackdropPoints.length} binned measurements digitized from ` +
      "Agazie et al. 2023, Fig 1c — <em>illustrative</em>, shown for context only."
    : "(No digitized 2023 measurement points loaded yet — the black analytic curve is " +
      "exact regardless. See DATA-SOURCES.md §3.)";
}

// Footer: attribution + independence disclaimer.
if (footer) {
  footer.innerHTML = `${ATTRIBUTION} Formula: Hellings &amp; Downs 1983, ApJL 265, L39.`;
}

// Initial paint.
syncViews();

// ---------------------------------------------------------------------------
// M2 — single-source residual sandbox
// ---------------------------------------------------------------------------
// A handful of recognizable, sky-spread pulsars whose induced residuals we draw. Falls
// back to an even spread if the preferred names aren't in the loaded set.
function pickResidualPulsars(all: Pulsar[], n = 6): Pulsar[] {
  const preferred = [
    "J1909-3744",
    "J1713+0747",
    "J0437-4715",
    "J1744-1134",
    "J0030+0451",
    "J1640+2224",
  ];
  const byName = new Map(all.map((p) => [p.name, p]));
  const chosen: Pulsar[] = [];
  const seen = new Set<string>();
  for (const nm of preferred) {
    const p = byName.get(nm);
    if (p && !seen.has(p.name)) {
      chosen.push(p);
      seen.add(p.name);
    }
    if (chosen.length >= n) break;
  }
  const step = Math.max(1, Math.floor(all.length / n));
  for (let i = 0; i < all.length && chosen.length < n; i += step) {
    const p = all[i];
    if (!seen.has(p.name)) {
      chosen.push(p);
      seen.add(p.name);
    }
  }
  return chosen.slice(0, n);
}

const residPlotEl = document.getElementById("resid-plot");
const residNote = document.getElementById("resid-note");
const srcMass = document.getElementById("src-mass") as HTMLInputElement | null;
const srcFreq = document.getElementById("src-freq") as HTMLInputElement | null;
const srcRa = document.getElementById("src-ra") as HTMLInputElement | null;
const srcDec = document.getElementById("src-dec") as HTMLInputElement | null;
const srcInc = document.getElementById("src-inc") as HTMLInputElement | null;
const srcMassOut = document.getElementById("src-mass-out");
const srcFreqOut = document.getElementById("src-freq-out");
const srcRaOut = document.getElementById("src-ra-out");
const srcDecOut = document.getElementById("src-dec-out");
const srcIncOut = document.getElementById("src-inc-out");
const src2Enable = document.getElementById("src2-enable") as HTMLInputElement | null;
const src2Controls = document.getElementById("src2-controls");
const src2Mass = document.getElementById("src2-mass") as HTMLInputElement | null;
const src2Freq = document.getElementById("src2-freq") as HTMLInputElement | null;
const src2Ra = document.getElementById("src2-ra") as HTMLInputElement | null;
const src2Dec = document.getElementById("src2-dec") as HTMLInputElement | null;
const src2MassOut = document.getElementById("src2-mass-out");
const src2FreqOut = document.getElementById("src2-freq-out");
const src2RaOut = document.getElementById("src2-ra-out");
const src2DecOut = document.getElementById("src2-dec-out");
const srcNoise = document.getElementById("src-noise") as HTMLInputElement | null;
const srcNoiseOut = document.getElementById("src-noise-out");

if (residPlotEl && pulsars.length >= 2) {
  const residPulsars = pickResidualPulsars(pulsars);

  /** Read the five sliders into a SourceParams (distance fixed; it only scales amplitude). */
  function readSourceParams(): SourceParams {
    const massLog = srcMass ? parseFloat(srcMass.value) : 9;
    const freqNHz = srcFreq ? parseFloat(srcFreq.value) : 10;
    const raDeg = srcRa ? parseFloat(srcRa.value) : 180;
    const decDeg = srcDec ? parseFloat(srcDec.value) : 0;
    const incDeg = srcInc ? parseFloat(srcInc.value) : 45;
    return {
      chirpMassSolar: Math.pow(10, massLog),
      distanceMpc: 50,
      freqHz: freqNHz * 1e-9,
      source: { raDeg, decDeg },
      inclinationRad: incDeg * DEG2RAD,
      psiRad: 0,
      phase0Rad: 0,
    };
  }

  function updateReadouts(p: SourceParams) {
    if (srcMassOut)
      srcMassOut.textContent = `${p.chirpMassSolar.toExponential(1).replace("e+", "×10^")} M☉`;
    if (srcFreqOut) {
      const nHz = p.freqHz * 1e9;
      const periodYr = 1 / p.freqHz / SECONDS_PER_YEAR;
      srcFreqOut.textContent = `${nHz.toFixed(1)} nHz · ${periodYr.toFixed(1)} yr`;
    }
    if (srcRaOut) srcRaOut.textContent = `${p.source.raDeg.toFixed(0)}°`;
    if (srcDecOut) srcDecOut.textContent = `${p.source.decDeg.toFixed(0)}°`;
    if (srcIncOut)
      srcIncOut.textContent = `${Math.round(p.inclinationRad / DEG2RAD)}°`;
  }

  // Optional second binary (superposition). Fixed inclination/ψ to keep its control set
  // compact; a different default phase so the two waveforms visibly interleave.
  function readSource2Params(): SourceParams {
    const massLog = src2Mass ? parseFloat(src2Mass.value) : 8.7;
    const freqNHz = src2Freq ? parseFloat(src2Freq.value) : 22;
    const raDeg = src2Ra ? parseFloat(src2Ra.value) : 60;
    const decDeg = src2Dec ? parseFloat(src2Dec.value) : 55;
    return {
      chirpMassSolar: Math.pow(10, massLog),
      distanceMpc: 50,
      freqHz: freqNHz * 1e-9,
      source: { raDeg, decDeg },
      inclinationRad: 45 * DEG2RAD,
      psiRad: 0,
      phase0Rad: 1.2,
    };
  }

  const source2Enabled = () => !!src2Enable?.checked;

  function buildSources(): SourceParams[] {
    const list = [readSourceParams()];
    if (source2Enabled()) list.push(readSource2Params());
    return list;
  }

  function updateReadouts2(p: SourceParams) {
    if (src2MassOut)
      src2MassOut.textContent = `${p.chirpMassSolar.toExponential(1).replace("e+", "×10^")} M☉`;
    if (src2FreqOut) {
      const nHz = p.freqHz * 1e9;
      const periodYr = 1 / p.freqHz / SECONDS_PER_YEAR;
      src2FreqOut.textContent = `${nHz.toFixed(1)} nHz · ${periodYr.toFixed(1)} yr`;
    }
    if (src2RaOut) src2RaOut.textContent = `${p.source.raDeg.toFixed(0)}°`;
    if (src2DecOut) src2DecOut.textContent = `${p.source.decDeg.toFixed(0)}°`;
  }

  function sourceMarkers() {
    const two = source2Enabled();
    const markers = [{ ...readSourceParams().source, label: two ? "source 1" : "GW source" }];
    if (two) markers.push({ ...readSource2Params().source, label: "source 2" });
    return markers;
  }

  const readNoise = () => (srcNoise ? Math.max(0, parseFloat(srcNoise.value)) : 0);

  let lastInfo = { peakNs: 0, nAboveNoise: 0, total: residPulsars.length };
  function renderNote() {
    if (!residNote) return;
    const two = source2Enabled();
    const rms = readNoise();
    const { peakNs, nAboveNoise, total } = lastInfo;
    const peakStr = peakNs < 10 ? peakNs.toFixed(1) : String(Math.round(peakNs));
    const srcClause = two
      ? "Two binaries, residuals <em>superposed</em> (general relativity is linear). "
      : "Earth-term only — the correlated part. ";
    const noiseClause =
      rms > 0
        ? `Against <strong>±${Math.round(rms)} ns</strong> of per-measurement timing ` +
          `noise, ${nAboveNoise} of ${total} pulsars poke clear of the band — yet a real ` +
          "PTA integrates ~15 yr across dozens of pulsars, so the 2023 detection pulled the " +
          "signal out from <em>below</em> this noise. "
        : "";
    residNote.innerHTML =
      `Showing ${total} pulsars; strongest induced residual <strong>≈ ${peakStr} ns</strong>. ` +
      srcClause +
      noiseClause +
      "Each pulsar shares each source's period, scaled and signed by its antenna pattern; " +
      "amplitude also scales with distance (fixed at 50 Mpc here).";
  }

  const residPanel = renderResidualPanel(residPlotEl, {
    pulsars: residPulsars,
    initialSources: buildSources(),
    initialRmsNs: readNoise(),
    onRender: (info) => {
      lastInfo = info;
      renderNote();
    },
  });

  function refresh() {
    updateReadouts(readSourceParams());
    if (source2Enabled()) updateReadouts2(readSource2Params());
    if (src2Controls) src2Controls.hidden = !source2Enabled();
    const rms = readNoise();
    if (srcNoiseOut) srcNoiseOut.textContent = rms > 0 ? `±${Math.round(rms)} ns` : "off";
    residPanel.update(buildSources(), rms);
    skymap?.setSources(sourceMarkers());
  }

  refresh();

  for (const el of [srcMass, srcFreq, srcRa, srcDec, srcInc, src2Mass, src2Freq, src2Ra, src2Dec, srcNoise]) {
    el?.addEventListener("input", refresh);
  }
  src2Enable?.addEventListener("change", refresh);
}

// ---------------------------------------------------------------------------
// Annotation layer — a "?" beside each control opens a plain-language note.
// Physically grounded, lay-audience wording; collapsed by default.
// ---------------------------------------------------------------------------
const ANNOTATIONS: Annotation[] = [
  {
    control: "theta-slider",
    title: "the angle θ",
    html:
      "The one thing the Hellings–Downs curve depends on: the angle between two pulsars " +
      "as seen from Earth. <strong>0°</strong> is the same direction on the sky, " +
      "<strong>180°</strong> is opposite sides. The striking claim of the 2023 result is " +
      "that this angle <em>alone</em> predicts how similarly any two pulsars wiggle.",
  },
  {
    control: "src-mass",
    html:
      "The <em>chirp mass</em> blends the two black holes' masses into the single number " +
      "that sets how <strong>loud</strong> the gravitational wave is — bigger mass, bigger " +
      "residual (amplitude grows as mass<sup>5/3</sup>). Supermassive binaries live around " +
      "10<sup>8</sup>–10<sup>10</sup> solar masses; the slider is logarithmic.",
  },
  {
    control: "src-freq",
    html:
      "How fast the binary spirals, which fixes the <strong>period</strong> of the wiggle " +
      "(period = 1 ⁄ frequency). Pulsar arrays listen in the <em>nanohertz</em> band — " +
      "periods of years to decades. Lower frequency ⇒ a slower, longer wave.",
  },
  {
    control: "src-ra",
    title: "the source's sky position",
    html:
      "Where the binary sits on the sky (right ascension). This is pure <strong>geometry</strong>: " +
      "each pulsar responds through its own “antenna pattern”, which depends on its angle to " +
      "the source — so moving the source changes <em>which</em> pulsars wiggle hardest. Watch " +
      "the gold ★ move on the map in §1.",
  },
  {
    control: "src-dec",
    title: "the source's sky position",
    html:
      "The other sky coordinate (declination, north–south). Together with RA it sets the " +
      "source's direction, and therefore each pulsar's antenna response — the geometry behind " +
      "why the residual amplitudes differ from pulsar to pulsar.",
  },
  {
    control: "src-inc",
    html:
      "The tilt of the binary's orbital plane to our line of sight: <strong>face-on</strong> " +
      "(0°) versus <strong>edge-on</strong> (90°). The two orientations emit the gravitational " +
      "wave's two polarizations in different proportions, changing the residual's size and shape.",
  },
  {
    control: "src2-enable",
    title: "a second binary",
    html:
      "A real background is <em>many</em> binaries at once. Because general relativity is " +
      "linear, their residuals simply <strong>add</strong>. Turn this on to watch two periods " +
      "beat together — the honest bridge from “one source” toward “a background of many”.",
  },
  {
    control: "src-noise",
    title: "timing noise",
    html:
      "Every measured pulse-arrival time carries scatter. Notice that a single measurement's " +
      "noise can <strong>swamp</strong> the signal — real detection comes from averaging " +
      "thousands of arrival times across ~15 years and dozens of pulsars, which is how the " +
      "2023 result dug the correlation out from <em>below</em> the per-measurement noise.",
  },
];
attachAnnotations(ANNOTATIONS);

// eslint-disable-next-line no-console
console.log(
  `[pta-explainer] M1 Live Demo up. ${pulsars.length} pulsar(s) loaded` +
    `${isPlaceholderData ? " (PLACEHOLDER set)" : ""}; ` +
    `${hasBackdropPoints ? hdBackdropPoints.length : 0} backdrop point(s).`,
);
