/**
 * @vitest-environment jsdom
 *
 * INTEGRATION: the §3 monopole/dipole reference overlays actually render into the SVG and
 * respond to the toggle. Unlike the other integration suites (which assert physics wiring
 * only), this one renders the real `HDCurvePlot` D3 component in a jsdom DOM and checks that:
 *   • both overlay curves are drawn (real path geometry) but HIDDEN by default;
 *   • `setOverlays(...)` shows/hides each overlay curve AND its legend row independently.
 * This guards the pedagogy fix end-to-end: the overlays exist and are toggleable, off by
 * default so the primary Hellings–Downs view stays clean.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { renderHDCurvePlot } from "../../components/HDCurvePlot";

function mount() {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const controller = renderHDCurvePlot(container, { initialThetaDeg: 30 });
  return { container, controller };
}

beforeEach(() => {
  document.body.innerHTML = "";
});

describe("§3 HD plot renders the monopole/dipole overlays", () => {
  it("draws an SVG with the HD curve, a marker, and both overlay paths", () => {
    const { container } = mount();
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(container.querySelector(".hd-marker")).not.toBeNull();
    expect(container.querySelector(".hd-overlay-monopole")).not.toBeNull();
    expect(container.querySelector(".hd-overlay-dipole")).not.toBeNull();
  });

  it("gives each overlay real path geometry (a non-empty 'd')", () => {
    const { container } = mount();
    const mono = container.querySelector(".hd-overlay-monopole");
    const dip = container.querySelector(".hd-overlay-dipole");
    // d3-shape emits an "M…L…" path string even without a live layout engine.
    expect(mono?.getAttribute("d") ?? "").toMatch(/^M/);
    expect(dip?.getAttribute("d") ?? "").toMatch(/^M/);
  });

  it("hides both overlays (and their legend rows) by default", () => {
    const { container } = mount();
    expect(container.querySelector(".hd-overlay-monopole")?.getAttribute("display")).toBe("none");
    expect(container.querySelector(".hd-overlay-dipole")?.getAttribute("display")).toBe("none");
    expect(container.querySelector(".hd-legend-monopole")?.getAttribute("display")).toBe("none");
    expect(container.querySelector(".hd-legend-dipole")?.getAttribute("display")).toBe("none");
  });

  it("shows the monopole overlay + legend row when toggled on, dipole still hidden", () => {
    const { container, controller } = mount();
    controller.setOverlays({ monopole: true });
    expect(container.querySelector(".hd-overlay-monopole")?.getAttribute("display")).not.toBe("none");
    expect(container.querySelector(".hd-legend-monopole")?.getAttribute("display")).not.toBe("none");
    // dipole untouched
    expect(container.querySelector(".hd-overlay-dipole")?.getAttribute("display")).toBe("none");
    expect(container.querySelector(".hd-legend-dipole")?.getAttribute("display")).toBe("none");
  });

  it("shows both overlays when both are toggled on, then hides them again", () => {
    const { container, controller } = mount();

    controller.setOverlays({ monopole: true, dipole: true });
    expect(container.querySelector(".hd-overlay-monopole")?.getAttribute("display")).not.toBe("none");
    expect(container.querySelector(".hd-overlay-dipole")?.getAttribute("display")).not.toBe("none");
    expect(container.querySelector(".hd-legend-dipole")?.getAttribute("display")).not.toBe("none");

    controller.setOverlays({ monopole: false, dipole: false });
    expect(container.querySelector(".hd-overlay-monopole")?.getAttribute("display")).toBe("none");
    expect(container.querySelector(".hd-overlay-dipole")?.getAttribute("display")).toBe("none");
  });

  it("leaves each overlay's state independent across partial updates", () => {
    const { container, controller } = mount();
    controller.setOverlays({ dipole: true }); // only dipole
    expect(container.querySelector(".hd-overlay-monopole")?.getAttribute("display")).toBe("none");
    expect(container.querySelector(".hd-overlay-dipole")?.getAttribute("display")).not.toBe("none");

    controller.setOverlays({ monopole: true }); // add monopole, dipole must stay on
    expect(container.querySelector(".hd-overlay-monopole")?.getAttribute("display")).not.toBe("none");
    expect(container.querySelector(".hd-overlay-dipole")?.getAttribute("display")).not.toBe("none");
  });
});
