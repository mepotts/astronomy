# M7 dry-run id sets

- built: 2026-08-23T19:12:36Z
- SET A `setA_queue981.csv`: the 981 day-one queue members; **74 (7.5%) have DR3 epoch photometry** (`gaiadr3.gaia_source.has_epoch_photometry`).
- SET B `setB_payload_stratified981.csv`: 981 DR3 sources in `nss_two_body_orbit` that also serve epoch photometry, composed into payload-homogeneous batches of 20 cycling five `num_selected_g_fov` strata (20-35, 35-50, 50-70, 70-100, 100-400).
- Why SET B exists: M6's throughput band is a two-model ambiguity created by a probe in which source count and payload bytes moved together. Holding n fixed at 20 while payload varies across batches decorrelates them.
