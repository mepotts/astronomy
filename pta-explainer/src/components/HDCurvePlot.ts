/**
 * The Hellings–Downs curve plot (M1: interactive).
 *
 * Renders SVG axes + the analytic H–D curve, the (optional) digitized 2023 NANOGrav
 * binned points as an "illustrative" backdrop, and a MARKER that rides the curve at the
 * currently-selected angular separation θ. The marker is draggable along the x-axis
 * (d3-drag): dragging it reports a new θ back to the caller via `onThetaChange`, which
 * keeps it in sync with the θ slider and the sky-map pair picker.
 *
 * The component is "dumb": it never owns θ. The caller owns θ (in main.ts) and calls
 * `update(thetaDeg)` to move the marker; the component only *requests* changes via the
 * callback while the user drags. This one-way data-flow keeps slider ⇄ map ⇄ curve in
 * sync without circular updates.
 */
import { scaleLinear } from "d3-scale";
import { axisBottom, axisLeft } from "d3-axis";
import { line } from "d3-shape";
import { select } from "d3-selection";
import { drag } from "d3-drag";
import { sampleHDCurve, hellingsDownsDeg } from "../physics/hellingsDowns";
import { sampleMonopoleCurve, sampleDipoleCurve } from "../physics/overlapReduction";

/** One digitized binned correlation point from the published figure. */
export interface HDPoint {
  thetaDeg: number;
  corr: number;
  /** Lower 1σ error-bar value (absolute corr), optional. */
  errLo?: number;
  /** Upper 1σ error-bar value (absolute corr), optional. */
  errHi?: number;
}

/** Which illustrative reference overlays to show alongside the HD quadrupole. */
export interface HDOverlayState {
  /** Clock/timing-error monopole (flat line). */
  monopole?: boolean;
  /** Solar-system ephemeris-error dipole (∝ cos θ). */
  dipole?: boolean;
}

export interface HDCurveController {
  /** Move the marker to a new angular separation (degrees, clamped to [0,180]). */
  update(thetaDeg: number): void;
  /**
   * Show/hide the illustrative monopole (clock errors) and dipole (ephemeris errors)
   * reference shapes. Both are off by default so the primary HD view stays clean.
   */
  setOverlays(state: HDOverlayState): void;
}

export interface HDCurveOptions {
  /** Optional digitized backdrop points (shown faint, labeled "illustrative"). */
  backdropPoints?: HDPoint[];
  /** Called continuously while the user drags the marker; receives θ in degrees. */
  onThetaChange?: (thetaDeg: number) => void;
  /** Initial angular separation in degrees. */
  initialThetaDeg?: number;
}

const clampTheta = (t: number) => (t < 0 ? 0 : t > 180 ? 180 : t);

export function renderHDCurvePlot(
  container: HTMLElement,
  options: HDCurveOptions = {},
): HDCurveController {
  const { backdropPoints, onThetaChange } = options;
  let theta = clampTheta(options.initialThetaDeg ?? 0);

  const width = 720;
  const height = 420;
  const margin = { top: 20, right: 24, bottom: 52, left: 60 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  const x = scaleLinear().domain([0, 180]).range([0, innerW]);
  const y = scaleLinear().domain([-0.5, 1.0]).range([innerH, 0]);

  const svg = select(container)
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("width", "100%")
    .attr("role", "img")
    .attr("aria-label", "Hellings-Downs correlation versus angular separation");

  const g = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // zero line
  g.append("line")
    .attr("x1", 0)
    .attr("x2", innerW)
    .attr("y1", y(0))
    .attr("y2", y(0))
    .attr("stroke", "#bbb")
    .attr("stroke-dasharray", "3 3");

  // axes
  g.append("g")
    .attr("transform", `translate(0,${innerH})`)
    .call(axisBottom(x).ticks(7));
  g.append("g").call(axisLeft(y).ticks(6));

  // axis labels
  g.append("text")
    .attr("x", innerW / 2)
    .attr("y", innerH + 42)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("Angle between the two pulsars on the sky, θ (degrees)");

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -innerH / 2)
    .attr("y", -44)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("How similarly they wiggle  (correlation)");

  // --- digitized backdrop points (optional, illustrative) ---
  if (backdropPoints && backdropPoints.length > 0) {
    const bg = g.append("g").attr("class", "hd-backdrop");
    // error bars
    bg.selectAll("line.hd-err")
      .data(backdropPoints.filter((p) => p.errLo != null && p.errHi != null))
      .join("line")
      .attr("class", "hd-err")
      .attr("x1", (d) => x(d.thetaDeg))
      .attr("x2", (d) => x(d.thetaDeg))
      .attr("y1", (d) => y(d.errLo as number))
      .attr("y2", (d) => y(d.errHi as number))
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 1)
      .attr("opacity", 0.5);
    // points
    bg.selectAll("circle.hd-pt")
      .data(backdropPoints)
      .join("circle")
      .attr("class", "hd-pt")
      .attr("cx", (d) => x(d.thetaDeg))
      .attr("cy", (d) => y(d.corr))
      .attr("r", 3)
      .attr("fill", "#3b82f6")
      .attr("opacity", 0.6);
  }

  // Shared line generator for the analytic curve + the reference overlays.
  const path = line<{ thetaDeg: number; corr: number }>()
    .x((d) => x(d.thetaDeg))
    .y((d) => y(d.corr));

  // --- illustrative reference overlays (monopole / dipole), hidden by default ---
  // Distinct colours (Okabe–Ito) + dash styles so they never read as the exact HD curve.
  // Drawn BEFORE the HD curve so the quadrupole (the headline) sits visually on top.
  const OVERLAY_MONO_COLOR = "#e69f00"; // orange — clock/timing errors (monopole)
  const OVERLAY_DIP_COLOR = "#009e73"; // bluish green — ephemeris errors (dipole)

  const monopolePath = g
    .append("path")
    .attr("class", "hd-overlay hd-overlay-monopole")
    .attr("fill", "none")
    .attr("stroke", OVERLAY_MONO_COLOR)
    .attr("stroke-width", 2)
    .attr("stroke-dasharray", "7 5")
    .attr("display", "none")
    .attr("d", path(sampleMonopoleCurve(181)));

  const dipolePath = g
    .append("path")
    .attr("class", "hd-overlay hd-overlay-dipole")
    .attr("fill", "none")
    .attr("stroke", OVERLAY_DIP_COLOR)
    .attr("stroke-width", 2)
    .attr("stroke-dasharray", "2 4")
    .attr("display", "none")
    .attr("d", path(sampleDipoleCurve(361)));

  // --- the analytic Hellings–Downs curve ---
  const curveData = sampleHDCurve(361);

  g.append("path")
    .datum(curveData)
    .attr("fill", "none")
    .attr("stroke", "#1a1a1a")
    .attr("stroke-width", 2)
    .attr("d", path);

  // --- legend (top-left, in the empty upper band above the curve) ---
  // The HD row is always shown; each overlay's legend row appears only while it is toggled on.
  const legend = g.append("g").attr("class", "hd-legend").attr("font-size", 11);
  const legendRow = (
    i: number,
    color: string,
    dash: string | null,
    label: string,
    cls?: string,
  ) => {
    const row = legend
      .append("g")
      .attr("transform", `translate(0,${i * 16 + 4})`);
    if (cls) row.attr("class", cls).attr("display", "none");
    row
      .append("line")
      .attr("x1", 0)
      .attr("x2", 22)
      .attr("y1", 0)
      .attr("y2", 0)
      .attr("stroke", color)
      .attr("stroke-width", cls ? 2 : 2.5)
      .attr("stroke-dasharray", dash);
    row
      .append("text")
      .attr("x", 28)
      .attr("y", 3.5)
      .attr("fill", "#1a1a1a")
      .text(label);
    return row;
  };
  legendRow(0, "#1a1a1a", null, "GW background — quadrupole (Hellings–Downs)");
  const monoLegend = legendRow(
    1,
    OVERLAY_MONO_COLOR,
    "7 5",
    "Clock errors — monopole (flat)",
    "hd-legend-monopole",
  );
  const dipLegend = legendRow(
    2,
    OVERLAY_DIP_COLOR,
    "2 4",
    "Ephemeris errors — dipole (∝ cos θ)",
    "hd-legend-dipole",
  );

  // --- the live marker that rides the curve ---
  // vertical guide from x-axis up to the marker
  const guide = g
    .append("line")
    .attr("class", "hd-guide")
    .attr("stroke", "#e11d48")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "2 2");

  const marker = g
    .append("circle")
    .attr("class", "hd-marker")
    .attr("r", 7)
    .attr("fill", "#e11d48")
    .attr("stroke", "#fff")
    .attr("stroke-width", 2)
    .style("cursor", "ew-resize");

  // floating readout label near the marker
  const readout = g
    .append("text")
    .attr("class", "hd-readout")
    .attr("text-anchor", "middle")
    .attr("fill", "#e11d48");

  function place(thetaDeg: number) {
    theta = clampTheta(thetaDeg);
    const corr = hellingsDownsDeg(theta);
    const px = x(theta);
    const py = y(corr);
    marker.attr("cx", px).attr("cy", py);
    guide.attr("x1", px).attr("x2", px).attr("y1", innerH).attr("y2", py);
    // keep the readout inside the plot horizontally
    const labelX = Math.min(Math.max(px, 36), innerW - 36);
    readout
      .attr("x", labelX)
      .attr("y", py - 14)
      .text(`θ = ${theta.toFixed(1)}°,  Γ = ${corr.toFixed(3)}`);
  }

  // drag along the x-axis → request a new θ from the caller
  const dragBehavior = drag<SVGCircleElement, unknown>().on("drag", (event) => {
    const newTheta = clampTheta(x.invert(event.x));
    place(newTheta);
    onThetaChange?.(newTheta);
  });
  marker.call(dragBehavior);

  // Overlay visibility state (both off by default → primary HD view stays clean).
  const overlays: Required<HDOverlayState> = { monopole: false, dipole: false };
  function applyOverlays() {
    monopolePath.attr("display", overlays.monopole ? null : "none");
    monoLegend.attr("display", overlays.monopole ? null : "none");
    dipolePath.attr("display", overlays.dipole ? null : "none");
    dipLegend.attr("display", overlays.dipole ? null : "none");
  }

  place(theta);
  applyOverlays();

  return {
    update(thetaDeg: number) {
      place(thetaDeg);
    },
    setOverlays(state: HDOverlayState) {
      if (state.monopole !== undefined) overlays.monopole = state.monopole;
      if (state.dipole !== undefined) overlays.dipole = state.dipole;
      applyOverlays();
    },
  };
}
