# stage3_vessel_size_sweep

This stage keeps the protocol fixed at 70 W x 10 min and explores the joint effect of:
- vessel gap: 0, 2, 5 mm
- vessel diameter: 3, 5, 8 mm

Outputs:
- `outputs/tables/stage3_gap_diameter_summary.csv`
- `outputs/figures/stage3_TCR_heatmap.png`
- `outputs/figures/stage3_MDI_heatmap.png`
- `outputs/figures/stage3_VUA_heatmap.png`
- `outputs/figures/stage3_eqdiam_heatmap.png`
- `outputs/figures/stage3_contour_panel_gap0.png`

Run:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
bash run_all.sh
```
