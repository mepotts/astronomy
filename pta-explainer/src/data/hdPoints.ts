/**
 * Typed access to the digitized Hellings–Downs backdrop points.
 *
 * These are the binned angular-separation-vs-correlation measurements from the 2023
 * NANOGrav evidence figure (Agazie et al. 2023, ApJL 951 L8, Fig 1c). They are NOT
 * published as a machine-readable table (DATA-SOURCES.md §3), so they must be
 * hand-digitized. Until that's done the array is EMPTY — the demo still works (the
 * analytic curve is exact); there is simply no illustrative backdrop overlay.
 *
 * When present, every point is shown faint and explicitly labeled "illustrative —
 * digitized from Agazie et al. 2023, Fig 1c" so it is never mistaken for the exact curve.
 */
import raw from "./nanograv15_hd_points.json";
import type { HDPoint } from "../components/HDCurvePlot";

export const hdBackdropPoints: HDPoint[] = raw as HDPoint[];

export const hasBackdropPoints: boolean = hdBackdropPoints.length > 0;
