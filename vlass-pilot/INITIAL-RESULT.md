# Initial acquisition result

**STOP_ACQUISITION, before any science pixels.** The first prospective protocol
requires corrected QL1.1 v2 provenance. CADC's one selected epoch-1.1 datalink
advertises a v1 artifact, not the required version. The protocol gate failed;
this does not itself establish whether CADC's pixels are actually uncorrected.
No version was inferred from its modification date and no flux was inspected.

The immutable initial `acquisition.json` records the exact metadata-only inputs,
hashes and error. Its `data/` files are retained locally and ignored. Thirteen
offline tests passed; synthetic recovery is not empirical validation.

A parent-authorized, separately frozen follow-up may use only epochs 2.1, 3.1
and 4.1. This excludes epoch 1 based on the documented version ambiguity before
any pixel measurements, not because a measured flux was inconvenient. It cannot
recover a historical FIRST-to-VLASS turn-on or prove the published fading rate.
