#!/usr/bin/env bash
set -e
export PYTHONPATH="$PWD/src"
python -m rfa_stage6_4.cli.make_figs6 --config configs/figure_style.yaml
