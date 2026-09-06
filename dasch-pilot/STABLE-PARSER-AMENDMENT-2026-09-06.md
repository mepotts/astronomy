# Empty-note representation correction

The literal original selection returned zero stars after downloading Table 3 and
ReadMe only; it is retained under `data/stable-20260906`. No DASCH curve had been
queried or inspected. Table 3 uses `---` (111 rows) as its no-comment placeholder,
not blank padding. The prospectively declared adapter treats exactly blank or
`---` as no note; every other original selection, identity and coverage rule stays
fixed. New run: `data/stable-normalized-20260906`; no overwriting the first result.
This is a parsing amendment after seeing metadata, not an outcome-driven change.
