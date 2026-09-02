#!/usr/bin/env bash
# M2 campaign launcher (H4): every run nice -n 19, BLAS threads pinned,
# logs under logs/, inventory under results/m2/manifest/.
# Usage:
#   scripts/m2_campaign.sh noise    # the top-10 noise campaign + J1909 extras
#   scripts/m2_campaign.sh fl       # the FL-CURN runs (after the campaign)
#   scripts/m2_campaign.sh one PSR KIND TAG WALL GATE SEED START [extra args]
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
mkdir -p results/m2/manifest logs

HEAVY="J1909-3744 J1600-3053 J1017-7156 J0437-4715"

launch () { # psr kind tag wall gate seed start [extra...]
    local psr=$1 kind=$2 tag=$3 wall=$4 gate=$5 seed=$6 start=$7; shift 7
    local th=1
    [[ " $HEAVY " == *" $psr "* ]] && th=4  # quiet-host bench: 97->43 ms
    local id="${psr}_${kind}_${tag}"
    # setsid: survive the launching session's death (nohup alone does NOT
    # shield against WSL session-tree teardown — measured, M2 doc 2.1);
    # the VM itself still needs one live session somewhere (keepalive).
    OMP_NUM_THREADS=$th OPENBLAS_NUM_THREADS=$th MKL_NUM_THREADS=$th \
    NUMEXPR_NUM_THREADS=$th VECLIB_MAXIMUM_THREADS=$th \
    setsid nohup nice -n 19 python scripts/m2_run.py "$psr" --kind "$kind" \
        --tag "$tag" --wall-min "$wall" --gate "$gate" --seed "$seed" \
        --start "$start" "$@" > "logs/${id}.log" 2>&1 &
    echo "launched ${id} pid=$! threads=${th}"
}

case "${1:-noise}" in
noise)
    # top-10 campaign (C1 gate 100k raw post-burn, 8 h wall cap each)
    launch J1713+0747 noise c1 480 100000 101 prior
    launch J2241-5236 noise c1 480 100000 102 prior
    launch J0437-4715 noise c1 480 100000 103 prior
    launch J1909-3744 noise blind1 480 100000 104 prior   # = campaign run
    launch J1744-1134 noise c1 480 100000 105 prior
    launch J0125-2327 noise c1 480 100000 106 prior
    launch J1946-5403 noise c1 480 100000 107 prior
    launch J1600-3053 noise c1 480 100000 108 prior
    launch J1017-7156 noise c1 480 100000 109 prior
    launch J2129-5721 noise c1 480 100000 110 prior
    # J1909 convergence extras (S-criteria)
    launch J1909-3744 noise blind2 480 100000 204 prior
    launch J1909-3744 noise informed 480 100000 304 published
    ;;
fl)
    # FL-CURN runs; whites fixed from each pulsar's own campaign summary
    i=0
    for psr in J1713+0747 J2241-5236 J0437-4715 J1744-1134 J0125-2327 \
               J1946-5403 J1600-3053 J1017-7156 J2129-5721; do
        i=$((i + 1))
        launch "$psr" fl fl1 240 50000 $((500 + i)) prior \
            --whites-from "results/m2/${psr}_noise_c1.summary.json"
    done
    launch J1909-3744 fl fl1 240 50000 510 prior \
        --whites-from "${J1909_WHITES:-results/m2/J1909-3744_noise_blind1.summary.json}"
    ;;
one)
    shift
    launch "$@"
    ;;
*)
    echo "unknown mode: $1" >&2; exit 2 ;;
esac
