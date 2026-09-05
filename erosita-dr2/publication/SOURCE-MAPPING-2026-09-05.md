# Scoped census counterpart mapping

This record documents the catalog fields already used by the 261-source census.
It does not fetch new data, reproduce the remote cross-match, or confirm a
physical counterpart. The compact package includes only those 261 rows of the
original mixed archival table, in `out/m2_archival_xray_census_only.csv`.

## Gaia classification

Source: [VizieR I/358/vclassre](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=I%2F358%2Fvclassre),
Gaia DR3 variability classification, cited to
[Rimoldini et al. 2023](https://arxiv.org/abs/2211.17238). This is not DSC.
The original `m2_archival_xray.py` configuration uses a 10-arcsec CDS XMatch
radius, groups by input row, and retains the smallest angular separation.

| Returned field | Census table column | Meaning |
|---|---|---|
| `Source` | `gclass_id` | Gaia source identifier |
| `Class` | `gclass_class` | Reported variability class |
| `ClassSc` | `gclass_score` | Reported classification score |
| `angDist` | `gclass_sep` | Nearest-match separation in arcsec |
| Match-row count per input | `gclass_n` | Number of returned matches within the query radius |

The census's AGN-like label is a heuristic based on the returned AGN/QSO class
or the CatWISE color criterion below. A nearest positional match is not a
probabilistically validated association; class scores do not establish X-ray
counterpart reliability. Empty values mean no value retained from that query,
not proof of physical absence or non-variability.

## CatWISE photometry

Source: [VizieR II/365/catwise](https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=II%2F365%2Fcatwise),
CatWISE2020 ([Marocco et al. 2021](https://arxiv.org/abs/2012.13084)); the same
10-arcsec/nearest-match rule applies.

| Returned field | Census table column |
|---|---|
| `Name` | `catwise_id` |
| `W1mproPM` | `catwise_w1` |
| `W2mproPM` | `catwise_w2` |
| `angDist` | `catwise_sep` |
| Match-row count per input | `catwise_n` |

The reported demographic cuts are W1-W2 >= 0.8 for the IR AGN-like branch and
W1 < 15 with |W1-W2| < 0.3 for the bright, IR-flat stellar branch. They are
descriptive classifications, not confirmed source types. The package omits
remote response caches, bulk inputs, and other candidate populations. See the
[publication closeout](../PUBLICATION-CLOSEOUT-2026-09-05.md) for those limitations.
