#!/usr/bin/env node
/**
 * ONE-OFF data-prep script (M1) — NOT run by the dev server.
 *
 * Reads the NANOGrav 15-year `.par` ephemeris files (downloaded from Zenodo 7967584
 * into a local, gitignored directory) and emits the tiny derived
 * `src/data/nanograv15_pulsars.json` the front-end ships with.
 *
 * Usage:
 *   node scripts/build-pulsars.mjs [parDir] [outFile]
 *
 *   parDir   directory to scan (recursively) for *.par files.
 *            Default: ./data/raw
 *   outFile  output JSON path.
 *            Default: ./src/data/nanograv15_pulsars.json
 *
 * Example, after unzipping the Zenodo release somewhere:
 *   node scripts/build-pulsars.mjs ./data/raw/narrowband/par
 *
 * What it does:
 *   1. Recursively finds every *.par file under parDir.
 *   2. Extracts the pulsar J-name (PSRJ / PSR) and J2000 position (RAJ/DECJ, or the
 *      decimal RAJD/DECJD, or ecliptic ELONG/ELAT as a fallback).
 *   3. Converts to decimal degrees (RA in [0,360), Dec in [-90,90]).
 *   4. De-duplicates (a pulsar may have both narrowband + wideband par files), sorts by
 *      RA, and writes the JSON array of { name, raDeg, decDeg }.
 *
 * The 15-yr GWB/Hellings–Downs analysis uses 67 pulsars; the full timing release has 68.
 * This script emits whatever it finds and prints the count so you can confirm 67/68.
 * See DATA-SOURCES.md §2.
 */
import { readFileSync, readdirSync, writeFileSync, statSync, existsSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..");

// --- coordinate conversion ------------------------------------------------

/** Sexagesimal RA "19:09:47.4348" (h:m:s) → degrees [0,360). */
function raHmsToDeg(raj) {
  const parts = raj.split(":").map(Number);
  const [h, m = 0, s = 0] = parts;
  if (![h, m, s].every(Number.isFinite)) return null;
  let deg = (h + m / 60 + s / 3600) * 15;
  // normalize into [0,360)
  deg = ((deg % 360) + 360) % 360;
  return deg;
}

/** Sexagesimal Dec "-37:44:14.46" (d:m:s) → degrees [-90,90], sign-aware. */
function decDmsToDeg(decj) {
  const t = decj.trim();
  // Sign must be read from the STRING (handles e.g. "-00:30:..." where degrees parse as 0).
  const sign = t.startsWith("-") ? -1 : 1;
  const parts = t.replace(/^[+-]/, "").split(":").map(Number);
  const [d, m = 0, s = 0] = parts;
  if (![d, m, s].every(Number.isFinite)) return null;
  return sign * (Math.abs(d) + m / 60 + s / 3600);
}

// Minimal ecliptic→equatorial fallback (some par files give ELONG/ELAT, not RAJ/DECJ).
// Obliquity of the ecliptic (J2000), degrees.
const OBLIQUITY_DEG = 23.4392911;
function eclipticToEquatorial(elongDeg, elatDeg) {
  const d2r = Math.PI / 180;
  const r2d = 180 / Math.PI;
  const eps = OBLIQUITY_DEG * d2r;
  const lon = elongDeg * d2r;
  const lat = elatDeg * d2r;
  const sinDec =
    Math.sin(lat) * Math.cos(eps) + Math.cos(lat) * Math.sin(eps) * Math.sin(lon);
  const dec = Math.asin(Math.max(-1, Math.min(1, sinDec)));
  const y = Math.sin(lon) * Math.cos(eps) - Math.tan(lat) * Math.sin(eps);
  const xx = Math.cos(lon);
  let ra = Math.atan2(y, xx);
  let raDeg = ((ra * r2d) % 360 + 360) % 360;
  return { raDeg, decDeg: dec * r2d };
}

// --- par parsing ----------------------------------------------------------

/** Pull the first whitespace-delimited token after a given key. */
function fieldValue(lines, key) {
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || trimmed.startsWith("C ")) continue;
    const toks = trimmed.split(/\s+/);
    if (toks[0] === key) return toks[1];
  }
  return undefined;
}

function parsePar(text) {
  const lines = text.split(/\r?\n/);
  const name = fieldValue(lines, "PSRJ") ?? fieldValue(lines, "PSR");

  const raj = fieldValue(lines, "RAJ");
  const decj = fieldValue(lines, "DECJ");
  if (name && raj && decj) {
    const raDeg = raHmsToDeg(raj);
    const decDeg = decDmsToDeg(decj);
    if (raDeg != null && decDeg != null) {
      return { name, raDeg: round4(raDeg), decDeg: round4(decDeg) };
    }
  }

  // Fallbacks: decimal-degree fields, then ecliptic.
  const rajd = fieldValue(lines, "RAJD");
  const decjd = fieldValue(lines, "DECJD");
  if (name && rajd && decjd && Number.isFinite(+rajd) && Number.isFinite(+decjd)) {
    return { name, raDeg: round4(+rajd), decDeg: round4(+decjd) };
  }

  const elong = fieldValue(lines, "ELONG");
  const elat = fieldValue(lines, "ELAT");
  if (name && elong && elat && Number.isFinite(+elong) && Number.isFinite(+elat)) {
    const { raDeg, decDeg } = eclipticToEquatorial(+elong, +elat);
    return { name, raDeg: round4(raDeg), decDeg: round4(decDeg) };
  }

  return null;
}

const round4 = (n) => +n.toFixed(4);

// --- file walking ---------------------------------------------------------

function findParFiles(dir) {
  const out = [];
  let entries;
  try {
    entries = readdirSync(dir);
  } catch {
    return out;
  }
  for (const entry of entries) {
    const full = join(dir, entry);
    let st;
    try {
      st = statSync(full);
    } catch {
      continue;
    }
    if (st.isDirectory()) {
      out.push(...findParFiles(full));
    } else if (entry.toLowerCase().endsWith(".par")) {
      out.push(full);
    }
  }
  return out;
}

// --- main -----------------------------------------------------------------

function main() {
  const parDir = process.argv[2] || join(REPO_ROOT, "data", "raw");
  const outFile =
    process.argv[3] || join(REPO_ROOT, "src", "data", "nanograv15_pulsars.json");

  if (!existsSync(parDir)) {
    console.error(`[build-pulsars] Par directory not found: ${parDir}`);
    console.error(
      "[build-pulsars] Download the NANOGrav 15-yr release from Zenodo 7967584,",
    );
    console.error(
      "[build-pulsars] unzip it, and point this script at the folder of .par files:",
    );
    console.error("[build-pulsars]   node scripts/build-pulsars.mjs <parDir> [outFile]");
    console.error(
      "[build-pulsars] (Existing src/data/nanograv15_pulsars.json left untouched.)",
    );
    process.exit(1);
  }

  const files = findParFiles(parDir);
  if (files.length === 0) {
    console.error(`[build-pulsars] No *.par files found under ${parDir}.`);
    process.exit(1);
  }
  console.error(`[build-pulsars] Found ${files.length} .par file(s) under ${parDir}.`);

  const byName = new Map();
  let skipped = 0;
  for (const file of files) {
    let parsed;
    try {
      parsed = parsePar(readFileSync(file, "utf8"));
    } catch (err) {
      console.error(`[build-pulsars]   ! failed to read ${file}: ${err.message}`);
      skipped++;
      continue;
    }
    if (!parsed) {
      skipped++;
      continue;
    }
    // De-dup: keep the first occurrence (narrowband/wideband give identical positions).
    if (!byName.has(parsed.name)) byName.set(parsed.name, parsed);
  }

  const pulsars = [...byName.values()].sort((a, b) => a.raDeg - b.raDeg);

  if (pulsars.length === 0) {
    console.error("[build-pulsars] Parsed 0 pulsars — check the par-file format.");
    process.exit(1);
  }

  writeFileSync(outFile, JSON.stringify(pulsars, null, 2) + "\n");
  console.error(
    `[build-pulsars] Wrote ${pulsars.length} pulsar(s) to ${outFile}` +
      (skipped ? ` (${skipped} file(s) skipped/duplicated).` : "."),
  );
  if (pulsars.length !== 67 && pulsars.length !== 68) {
    console.error(
      `[build-pulsars] NOTE: expected 67 (HD analysis) or 68 (full timing release); ` +
        `got ${pulsars.length}. Verify your par-file set.`,
    );
  }
  // Spot-check a couple of well-known pulsars if present (sanity vs SIMBAD).
  for (const want of ["J1909-3744", "J1713+0747"]) {
    const p = byName.get(want);
    if (p) console.error(`[build-pulsars]   spot-check ${p.name}: RA=${p.raDeg}°, Dec=${p.decDeg}°`);
  }
}

main();
