/**
 * Sky map of the pulsar array (M1).
 *
 * A D3 scatter of every pulsar by (RA, Dec). The user clicks two pulsars to form a
 * pair; the component highlights the pair, draws a connector between them, and reports
 * the pair back to the caller via `onPairSelected`, which converts it to an angular
 * separation θ that drives the H–D curve marker.
 *
 * Convention: right ascension increases to the LEFT (standard for an all-sky chart seen
 * looking outward), declination increases upward. We keep the axis labels plain-language
 * for a general audience but keep the real RA/Dec degrees on the ticks.
 *
 * Like the curve plot, this component does not own the "selected θ" — it only owns which
 * two pulsars are currently picked, and announces pair changes. The caller (main.ts) is
 * the single source of truth for θ.
 */
import { scaleLinear } from "d3-scale";
import { axisBottom, axisLeft } from "d3-axis";
import { select } from "d3-selection";
import type { Pulsar } from "../data/pulsars";

export interface SkyMapController {
  /** Programmatically set the selected pair (e.g. a "random pair" button). */
  setPair(a: Pulsar | null, b: Pulsar | null): void;
  /**
   * Show the gravitational-wave source marker(s) (M2) at the given sky positions (pass an
   * empty array to clear). Driven by the §4 source sliders so the geometry behind the
   * residual amplitudes is visible on the same sky map.
   */
  setSources(list: Array<{ raDeg: number; decDeg: number; label?: string }>): void;
}

export interface SkyMapOptions {
  /** Called whenever the selected pair changes (either index may be null). */
  onPairSelected?: (a: Pulsar | null, b: Pulsar | null) => void;
  /** Optional initial pair (names). */
  initialPair?: [string, string];
}

export function renderSkyMap(
  container: HTMLElement,
  pulsars: Pulsar[],
  options: SkyMapOptions = {},
): SkyMapController {
  const { onPairSelected } = options;

  const width = 720;
  const height = 360;
  const margin = { top: 16, right: 20, bottom: 48, left: 56 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  // RA 0..360 reversed (astronomical convention), Dec -90..90.
  const x = scaleLinear().domain([0, 360]).range([innerW, 0]);
  const y = scaleLinear().domain([-90, 90]).range([innerH, 0]);

  const svg = select(container)
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("width", "100%")
    .attr("role", "img")
    .attr("aria-label", "Sky map of the pulsar array; click two pulsars to pick a pair");

  const g = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // celestial-equator guide
  g.append("line")
    .attr("x1", 0)
    .attr("x2", innerW)
    .attr("y1", y(0))
    .attr("y2", y(0))
    .attr("stroke", "#eee");

  g.append("g")
    .attr("transform", `translate(0,${innerH})`)
    .call(axisBottom(x).ticks(7).tickFormat((d) => `${d}°`));
  g.append("g").call(axisLeft(y).ticks(7).tickFormat((d) => `${d}°`));

  g.append("text")
    .attr("x", innerW / 2)
    .attr("y", innerH + 42)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("Right ascension — position around the sky (degrees, increasing left)");

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -innerH / 2)
    .attr("y", -42)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("Declination — north/south (degrees)");

  // connector line between the selected pair (drawn behind the dots)
  const connector = g
    .append("line")
    .attr("class", "sky-connector")
    .attr("stroke", "#e11d48")
    .attr("stroke-width", 1.5)
    .attr("opacity", 0)
    .style("pointer-events", "none");

  // selection state
  let selA: Pulsar | null = null;
  let selB: Pulsar | null = null;

  function announce() {
    onPairSelected?.(selA, selB);
    redraw();
  }

  function selectPulsar(p: Pulsar) {
    // toggle off if clicking an already-selected one
    if (selA?.name === p.name) {
      selA = selB;
      selB = null;
    } else if (selB?.name === p.name) {
      selB = null;
    } else if (!selA) {
      selA = p;
    } else if (!selB) {
      selB = p;
    } else {
      // both full: start a new pair from this click
      selA = p;
      selB = null;
    }
    announce();
  }

  // the pulsar dots (with a transparent larger hit-target for easy clicking)
  const node = g
    .selectAll<SVGGElement, Pulsar>("g.pulsar")
    .data(pulsars, (d) => (d as Pulsar).name)
    .join("g")
    .attr("class", "pulsar")
    .attr("transform", (d) => `translate(${x(d.raDeg)},${y(d.decDeg)})`)
    .style("cursor", "pointer")
    .on("click", (_event, d) => selectPulsar(d));

  node.append("title").text((d) => d.name);

  node
    .append("circle")
    .attr("class", "hit")
    .attr("r", 9)
    .attr("fill", "transparent");

  node
    .append("circle")
    .attr("class", "dot")
    .attr("r", 4)
    .attr("fill", "#475569")
    .attr("stroke", "#fff")
    .attr("stroke-width", 1);

  // small labels (kept subtle; only shown for selected pulsars to avoid clutter)
  const label = node
    .append("text")
    .attr("class", "psr-label")
    .attr("x", 8)
    .attr("y", 4)
    .attr("fill", "#1a1a1a")
    .attr("font-size", 11)
    .style("pointer-events", "none")
    .style("opacity", 0)
    .text((d) => d.name);

  // GW source marker(s) (M2): gold stars driven by the §4 source sliders. Drawn on top of
  // the pulsar dots; non-interactive (the map's clicks stay dedicated to pulsar-pair
  // picking). Rendered from a list so a second binary shows as a second star.
  type SourceMarker = { raDeg: number; decDeg: number; label?: string };
  const sourcesG = g.append("g").attr("class", "gw-sources").style("pointer-events", "none");

  function renderSources(list: SourceMarker[]) {
    sourcesG
      .selectAll<SVGGElement, SourceMarker>("g.gw-source")
      .data(list)
      .join((enter) => {
        const ge = enter.append("g").attr("class", "gw-source");
        ge.append("circle").attr("r", 12).attr("fill", "#f59e0b").attr("opacity", 0.18);
        ge.append("text")
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "central")
          .attr("font-size", 19)
          .attr("fill", "#d97706")
          .text("★");
        ge.append("text")
          .attr("class", "gw-source-label")
          .attr("text-anchor", "middle")
          .attr("y", -15)
          .attr("font-size", 10.5)
          .attr("fill", "#b45309");
        return ge;
      })
      .attr("transform", (d) => `translate(${x(d.raDeg)},${y(d.decDeg)})`)
      .select<SVGTextElement>("text.gw-source-label")
      .text((d) => d.label ?? "GW source");
  }

  function isSelected(p: Pulsar): boolean {
    return selA?.name === p.name || selB?.name === p.name;
  }

  function redraw() {
    node
      .select<SVGCircleElement>("circle.dot")
      .attr("fill", (d) => (isSelected(d) ? "#e11d48" : "#475569"))
      .attr("r", (d) => (isSelected(d) ? 6 : 4));
    label.style("opacity", (d) => (isSelected(d) ? 1 : 0));

    if (selA && selB) {
      connector
        .attr("x1", x(selA.raDeg))
        .attr("y1", y(selA.decDeg))
        .attr("x2", x(selB.raDeg))
        .attr("y2", y(selB.decDeg))
        .attr("opacity", 0.9);
    } else {
      connector.attr("opacity", 0);
    }
  }

  // apply optional initial pair
  if (options.initialPair) {
    const [an, bn] = options.initialPair;
    selA = pulsars.find((p) => p.name === an) ?? null;
    selB = pulsars.find((p) => p.name === bn) ?? null;
  }
  redraw();

  return {
    setPair(a, b) {
      selA = a;
      selB = b;
      announce();
    },
    setSources(list) {
      renderSources(list);
    },
  };
}
