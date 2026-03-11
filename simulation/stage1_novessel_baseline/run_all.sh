
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

mkdir -p outputs/figures outputs/metrics outputs/cases outputs/tables
export PYTHONPATH="$PWD/src:${PYTHONPATH}"

python -m rfa_stage1.cli.preview_geometry --config configs/base.yaml
python -m rfa_stage1.cli.calibrate_source_scale --config configs/base.yaml --target-equivalent-diameter-mm 22 --search-min 4 --search-max 12 --num 17
python -m rfa_stage1.cli.run_case --config configs/base.yaml
python -m rfa_stage1.cli.sweep_novessel --base-config configs/base.yaml --sweep-config configs/sweep_novessel.yaml
