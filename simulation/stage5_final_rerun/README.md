# stage4_publishable

This stage bundles the minimum additions needed to move from a single-protocol exploratory model to a more publishable simulation study.

It runs:
1. A reference single-vessel case.
2. A dual-protocol sweep across vessel gap and vessel diameter.
   - balanced: 60 W x 10 min
   - aggressive: 70 W x 10 min
3. A numerical convergence check.
   - grid: 81, 121, 161
   - dt: 4, 2, 1 s
   - cases: no-vessel and severe-vessel (gap 0 mm, diameter 8 mm)

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
bash run_all.sh
```

## Main outputs
- `outputs/tables/stage4_protocol_gap_diameter_summary.csv`
- `outputs/figures/stage4_balanced_MDI_heatmap.png`
- `outputs/figures/stage4_aggressive_MDI_heatmap.png`
- `outputs/figures/stage4_compare_MDI_vs_gap_d5.png`
- `outputs/tables/stage4_convergence_summary.csv`

## Recommended paper framing
- Primary factor: vessel gap.
- Secondary factor: vessel diameter.
- Protocol dependence: balanced vs aggressive protocol.
- Credibility layer: grid/time-step sensitivity.
