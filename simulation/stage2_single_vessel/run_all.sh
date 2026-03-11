#!/usr/bin/env bash
set -e
export PYTHONPATH="$PWD/src"
python -m rfa_stage2.cli.preview_geometry --config configs/base.yaml
python -m rfa_stage2.cli.run_case --config configs/base.yaml
python -m rfa_stage2.cli.sweep_gap --config configs/base.yaml --gap-config configs/gap_sweep.yaml
