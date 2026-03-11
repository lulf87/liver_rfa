#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

mkdir -p outputs/figures outputs/metrics outputs/cases

export PYTHONPATH="$PWD/src:${PYTHONPATH}"

python -m rfa_stage0.cli.preview_geometry --config configs/base.yaml
python -m rfa_stage0.cli.calibrate_source_scale --config configs/base.yaml --target-equivalent-diameter-mm 22 --search-min 1 --search-max 1e4 --num 20
python -m rfa_stage0.cli.run_case --config configs/base.yaml
