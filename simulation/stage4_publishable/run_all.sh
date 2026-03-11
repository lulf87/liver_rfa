#!/usr/bin/env bash
set -e
export PYTHONPATH="$PWD/src"
python -m rfa_stage4.cli.preview_geometry --config configs/base.yaml
python -m rfa_stage4.cli.run_case --config configs/base.yaml
python -m rfa_stage4.cli.sweep_protocol_gap_diameter --config configs/base.yaml --sweep-config configs/protocols_gap_diameter_sweep.yaml
python -m rfa_stage4.cli.convergence_check --config configs/base.yaml --conv-config configs/convergence.yaml
