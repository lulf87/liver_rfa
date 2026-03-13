#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATCH_ROOT="$ROOT/stage6_8_label_unification_patch/patch_files"

cp -f "$PATCH_ROOT/stage6_1_paper_figures/src/rfa_stage6/paper_figures.py"       "$ROOT/stage6_1_paper_figures/src/rfa_stage6/paper_figures.py"

cp -f "$PATCH_ROOT/stage6_2_supplementary_figures/src/rfa_stage6_2/supplementary_figures.py"       "$ROOT/stage6_2_supplementary_figures/src/rfa_stage6_2/supplementary_figures.py"

cp -f "$PATCH_ROOT/stage6_4_shape_vs_size_fig/src/rfa_stage6_4/cli/make_figs6.py"       "$ROOT/stage6_4_shape_vs_size_fig/src/rfa_stage6_4/cli/make_figs6.py"

echo "Patched stage6_1, stage6_2, and stage6_4 label text."
echo "Now rerun the figure-generation stages to refresh output files."
