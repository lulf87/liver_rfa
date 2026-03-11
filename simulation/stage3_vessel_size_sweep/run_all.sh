#!/usr/bin/env bash
set -e
export PYTHONPATH="$PWD/src"
python -m rfa_stage3.cli.preview_geometry --config configs/base.yaml
python -m rfa_stage3.cli.run_case --config configs/base.yaml
python -m rfa_stage3.cli.sweep_gap_diameter --config configs/base.yaml --sweep-config configs/gap_diameter_sweep.yaml
