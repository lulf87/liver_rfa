#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$PWD/src"
python -m rfa_stage6_7.cli.make_absolute_damage_figure --config configs/figure_style.yaml
