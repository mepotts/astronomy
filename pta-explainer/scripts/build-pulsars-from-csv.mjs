#!/usr/bin/env node
/**
 * ONE-OFF data-prep script (M1) — NOT run by the dev server.
 *
 * Companion to `build-pulsars.mjs`. Where that script parses raw NANOGrav `.par`
 * ephemeris files, this one reads the already-resolved sky-position CSV that ships in
 * `data/raw/` and emits the tiny derived `src/data/nanograv15_pulsars.json` the
 * front-end ships with.
 *
 * The CSV (`data/raw/nanograv_15yr_67pulsars_positions.csv`) holds the 67 pulsars used
 * in the NANOGrav 15-yr Hellings–Downs angular-correlation analysis, with J2000
 * positions already converted to decimal degrees. 65 positions are precise (resolved
 * against the ATNF pulsar catalogue); 2 (J0406+3039, J0557+1551) are name-approximate
 * (derived from the J-name to ~degree precision — adequate for an illustrative sky map,
 * flagged via the `source` column == "NAME_APPROX").
 *
 * Usage:
 *   node scripts/build-pulsars-from-csv.mjs [csvFile] [outFile]
 *
 *   csvFile  CSV to read. Default: ./data/raw/nanograv_15yr_67pulsars_positions.csv
 *            Columns: name, RAJ, DECJ, RA_deg, Dec_deg, source
 *   outFile  output JSON path. Default: ./src/data/nanograv15_pulsars.json
 *
 * Output schema (identical to build-pulsars.mjs, so the front-end is unchanged):
 *   [ { "name": "J1909-3744", "raDeg": 287.4476, "decDeg": -37.7374 }, … 67 entries ]
 *
 * See DATA-SOURCES.md §2.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..");

const round4 = (n) => +n.toFixed(4);

/** Minimal CSV parser: splits on commas (this file has no quoted/embedded commas). */
function parseCsv(text) {
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== "");
  const header = lines[0].split(",").map((h) => h.trim());
  const idx = (key) => header.indexOf(key);
  const iName = idx("name");
  const iRa = idx("RA_deg");
  const iDec = idx("Dec_deg");
  const iSrc = idx("source");
  if (iName < 0 || iRa < 0 || iDec < 0) {
    throw new Error(
      `CSV missing required columns; need name, RA_deg, Dec_deg. Got: ${header.join(", ")}`,
    );
  }
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = lines[i].split(",");
    const name = (cells[iName] || "").trim();
    const raDeg = Number(cells[iRa]);
    const decDeg = Number(cells[iDec]);
    const source = iSrc >= 0 ? (cells[iSrc] || "").trim() : "";
    if (!name || !Number.isFinite(raDeg) || !Number.isFinite(decDeg)) continue;
    rows.push({ name, raDeg, decDeg, source });
  }
  return rows;
}

function main() {
  const csvFile =
    process.argv[2] ||
    join(REPO_ROOT, "data", "raw", "nanograv_15yr_67pulsars_positions.csv");
  const outFile =
    process.argv[3] || join(REPO_ROOT, "src", "data", "nanograv15_pulsars.json");

  if (!existsSync(csvFile)) {
    console.error(`[build-pulsars-from-csv] CSV not found: ${csvFile}`);
    process.exit(1);
  }

  const rows = parseCsv(readFileSync(csvFile, "utf8"));
  if (rows.length === 0) {
    console.error("[build-pulsars-from-csv] Parsed 0 rows — check the CSV format.");
    process.exit(1);
  }

  // De-dup by name (first occurrence wins), sort by RA to match build-pulsars.mjs.
  const byName = new Map();
  for (const r of rows) if (!byName.has(r.name)) byName.set(r.name, r);
  const approx = [...byName.values()].filter((r) => r.source === "NAME_APPROX");

  const pulsars = [...byName.values()]
    .map(({ name, raDeg, decDeg }) => ({
      name,
      raDeg: round4(raDeg),
      decDeg: round4(decDeg),
    }))
    .sort((a, b) => a.raDeg - b.raDeg);

  writeFileSync(outFile, JSON.stringify(pulsars, null, 2) + "\n");
  console.error(
    `[build-pulsars-from-csv] Wrote ${pulsars.length} pulsar(s) to ${outFile}.`,
  );
  if (approx.length) {
    console.error(
      `[build-pulsars-from-csv] NOTE: ${approx.length} name-approx position(s): ` +
        approx.map((r) => r.name).join(", "),
    );
  }
  if (pulsars.length !== 67 && pulsars.length !== 68) {
    console.error(
      `[build-pulsars-from-csv] NOTE: expected 67 (HD analysis) or 68 (full release); ` +
        `got ${pulsars.length}. Verify the CSV.`,
    );
  }
  for (const want of ["J1909-3744", "J1713+0747"]) {
    const p = pulsars.find((x) => x.name === want);
    if (p)
      console.error(
        `[build-pulsars-from-csv]   spot-check ${p.name}: RA=${p.raDeg}°, Dec=${p.decDeg}°`,
      );
  }
}

main();
