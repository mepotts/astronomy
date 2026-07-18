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

/** One digitized binned correlation point from the published figure. */
export interface HDPoint {
  thetaDeg: number;
  corr: number;
  /** Lower 1σ error-bar value (absolute corr), optional. */
  errLo?: number;
  /** Upper 1σ error-bar value (absolute corr), optional. */
  errHi?: number;
}

export interface HDCurveController {
  /** Move the marker to a new angular separation (degrees, clamped to [0,180]). */
  update(thetaDeg: number): void;
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

  // --- the analytic Hellings–Downs curve ---
  const curveData = sampleHDCurve(361);
  const path = line<{ thetaDeg: number; corr: number }>()
    .x((d) => x(d.thetaDeg))
    .y((d) => y(d.corr));

  g.append("path")
    .datum(curveData)
    .attr("fill", "none")
    .attr("stroke", "#1a1a1a")
    .attr("stroke-width", 2)
    .attr("d", path);

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

  place(theta);

  return {
    update(thetaDeg: number) {
      place(thetaDeg);
    },
  };
}
