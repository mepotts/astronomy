/**
 * Typed access to the baked-in pulsar array.
 *
 * The JSON ships in the bundle (no runtime fetch). In M0 this is a 6-pulsar
 * PLACEHOLDER; in M1 it is replaced by the real 67-pulsar NANOGrav 15-yr array
 * via `scripts/build-pulsars.mjs` (see DATA-SOURCES.md §2). The shape is identical
 * either way, so nothing downstream changes when the data is swapped.
 */
import raw from "./nanograv15_pulsars.json";

export interface Pulsar {
  /** PSR J-name, e.g. "J1909-3744". */
  name: string;
  /** Right ascension in decimal degrees [0, 360). */
  raDeg: number;
  /** Declination in decimal degrees [-90, 90]. */
  decDeg: number;
}

export const pulsars: Pulsar[] = raw as Pulsar[];

/**
 * True when the loaded array is the small hand-entered placeholder rather than the
 * full real NANOGrav set. Used to surface an honest "placeholder data" banner in the
 * UI. The real release uses 67 pulsars in the Hellings–Downs analysis; anything well
 * below that is the placeholder.
 */
export const isPlaceholderData: boolean = pulsars.length < 60;
