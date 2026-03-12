#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$ROOT/src"
export MPLCONFIGDIR="$ROOT/.mplconfig"
mkdir -p "$MPLCONFIGDIR"
python -m rfa_stage6_3.cli.make_refined_benchmark --config configs/figure_style.yaml
