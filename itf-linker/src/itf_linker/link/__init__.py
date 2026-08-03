"""M3: linking tracklets that nobody has connected.

M1 fitted the *cheap* population -- designations that already spanned three or more
nights under one trkSub, so the association work had already been done by a survey. This
package does the association itself: it proposes that tracklet *A*, tracklet *B* and
tracklet *C*, carrying three unrelated trkSubs and possibly three different observatory
codes, are one object.

The architecture is fixed by M0's headline measurement and is not negotiable: at
nside=64 x 3 days the ITF yields 15.4M candidate pairs but **753M triplets**, and coarser
partitions reach 10^11. Nothing here ever enumerates a triplet. The linker used is
HelioLinC (Holman et al. 2018; Heinze et al. 2022): under an assumed heliocentric
distance every tracklet is promoted to a full state vector, propagated to a common epoch,
and *clustered*. Cost is ``O(tracklets x hypotheses)``, and a cluster of any size falls
out of one pass -- three-night links are found without a three-way loop ever existing.

Modules:

``geometry``
    Observer positions, the line-of-sight/sphere intersection, the velocity solve, and
    two-body propagation. Pure numpy, no ITF knowledge.
``arrows``
    Tracklets with a fitted sky-plane rate ("arrows"), which is what HelioLinC consumes.
``heliolinc``
    The hypothesis grid, the clustering, and the candidate links that come out.
``pipeline``
    Windowing, orchestration, gating, and cross-observatory ranking.
``validate``
    The in-file ground truth M0 asked for: hide the trkSub linkage on the designations
    that already span 3+ nights and measure whether the linker rediscovers them.
"""

from __future__ import annotations

from .arrows import Arrows, build_arrows
from .assemble import gate_links, link_astrometry
from .heliolinc import HypothesisGrid, LinkCandidate, link_window
from .pipeline import link_arrows, link_slice
from .run import run_m3
from .validate import ground_truth_groups, score_links

__all__ = [
    "Arrows",
    "HypothesisGrid",
    "LinkCandidate",
    "build_arrows",
    "gate_links",
    "ground_truth_groups",
    "link_arrows",
    "link_astrometry",
    "link_slice",
    "link_window",
    "run_m3",
    "score_links",
]
