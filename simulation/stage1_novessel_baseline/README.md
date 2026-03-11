
# stage1_novessel_baseline

This stage builds a no-vessel baseline for the liver RFA toy model.

## Goal

Produce a baseline protocol map before turning on the vessel heat-sink effect.

## What this stage does

1. Preview geometry.
2. Run a no-vessel single case.
3. Run a small no-vessel power-time sweep.
4. Save per-case metrics, compressed fields, and heatmaps.

## Folder layout

```text
stage1_novessel_baseline/
├── src/
├── configs/
├── outputs/
├── requirements.txt
├── run_all.sh
└── README.md
```

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## Run all

```bash
bash run_all.sh
```

## Main outputs

- `outputs/figures/stage1_novessel_p50_t8_geometry.png`
- `outputs/figures/stage1_novessel_p50_t8_overview.png`
- `outputs/figures/heatmap_eq_diameter.png`
- `outputs/figures/heatmap_TCR.png`
- `outputs/figures/heatmap_MDI.png`
- `outputs/tables/novessel_summary.csv`
- `outputs/tables/recommended_case.json`

## Interpretation

A good no-vessel baseline should move toward:

- TCR close to 1.0
- low MDI
- VUA = 0.0

At this stage, VUA stays 0 because the vessel is disabled.
