/**
 * M2 annotation layer — per-control "what am I looking at?" help.
 *
 * For each registered control we tuck a small "?" toggle beside its label and, on demand,
 * reveal a plain-language note explaining what that knob does physically. Collapsed by
 * default so the page stays uncluttered for people who don't need it. Pure DOM + ARIA,
 * no framework — consistent with the rest of the app.
 *
 * Placement is layout-agnostic:
 *   • a control with a separate <label for> (the θ slider, the §4 source sliders, the noise
 *     slider) gets its label + toggle wrapped in one .label-cell so they share a single
 *     grid/flex slot; the note is inserted as a full-width row right below the control.
 *   • a control whose <input> is wrapped by its label (the "second binary" checkbox) gets
 *     the toggle as a sibling after the label, with the note below it.
 * The note carries `grid-column: 1 / -1` and `flex-basis: 100%` so it spans the full width
 * in either a grid (.source-controls) or flex (.controls) container, and is an ordinary
 * block anywhere else — one CSS rule covers all three.
 */

export interface Annotation {
  /** id of the control's <input>; its label is resolved from this. */
  control: string;
  /** Short lay explanation. May contain inline HTML (<em>, <strong>, <code>). */
  html: string;
  /** Accessible name for the toggle (e.g. "Chirp mass"). Defaults to the label text. */
  title?: string;
}

/** The element the note is inserted after: the control's row, or the wrapping label. */
function rowAnchor(input: HTMLElement, wrappingLabel: HTMLElement | null): Element {
  return (
    input.closest(".src-row") ??
    input.closest(".controls") ??
    wrappingLabel ??
    input.parentElement ??
    input
  );
}

function makeToggle(annId: string, title: string): HTMLButtonElement {
  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "ann-toggle";
  toggle.textContent = "?";
  toggle.setAttribute("aria-expanded", "false");
  toggle.setAttribute("aria-controls", annId);
  toggle.setAttribute("aria-label", `What is ${title}?`);
  toggle.title = `What is ${title}?`;
  return toggle;
}

/** Wire up "?" toggles + collapsible notes for each annotation. Missing controls are skipped. */
export function attachAnnotations(annotations: Annotation[]): number {
  let attached = 0;

  for (const a of annotations) {
    const input = document.getElementById(a.control);
    if (!input) continue;

    const explicitLabel = document.querySelector<HTMLElement>(`label[for="${a.control}"]`);
    const wrappingLabel = input.closest("label") as HTMLElement | null;
    const label = explicitLabel ?? wrappingLabel;
    if (!label) continue;

    const title = a.title ?? label.textContent?.trim() ?? a.control;
    const annId = `ann-${a.control}`;
    const toggle = makeToggle(annId, title);

    if (explicitLabel) {
      // Keep label text + toggle together in one grid/flex cell.
      const cell = document.createElement("span");
      cell.className = "label-cell";
      label.replaceWith(cell);
      cell.append(label, toggle);
    } else {
      // Input is wrapped by its label (checkbox): toggle sits right after the label.
      label.after(toggle);
    }

    const note = document.createElement("div");
    note.className = "annotation";
    note.id = annId;
    note.setAttribute("role", "note");
    note.hidden = true;
    note.innerHTML = a.html;

    // Insert the note as a full-width row below the control (or below the toggle, for the
    // wrapping-label case, so DOM order stays label → toggle → note).
    (explicitLabel ? rowAnchor(input, wrappingLabel) : toggle).after(note);

    toggle.addEventListener("click", () => {
      const opening = note.hidden;
      note.hidden = !opening;
      toggle.setAttribute("aria-expanded", String(opening));
    });

    attached += 1;
  }

  return attached;
}
