# stage2_single_vessel

Purpose: first near-vessel heat-sink experiment on top of a calibrated no-vessel baseline.

## Default protocol
- power: 70 W
- time: 10 min
- source_scale_per_W: 7.5
- vessel diameter: 5 mm
- gap sweep: 0, 1, 2, 3, 5 mm

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
bash run_all.sh
```

## Outputs
- `outputs/figures/stage2_single_vessel_reference_geometry.png`
- `outputs/figures/stage2_single_vessel_reference_overview.png`
- `outputs/figures/stage2_TCR_vs_gap.png`
- `outputs/figures/stage2_MDI_vs_gap.png`
- `outputs/figures/stage2_VUA_vs_gap.png`
- `outputs/figures/stage2_lesion_contour_panel.png`
- `outputs/tables/stage2_gap_sweep_summary.csv`
- `outputs/metrics/*.json`

## Notes
This stage fixes the calibration constant to 7.5 based on the stage1 calibration result.
To test a more conservative baseline, edit `configs/base.yaml` and change:
- `nominal_power_W: 60.0`
- `ablation_time_s: 600.0`
then rerun `bash run_all.sh`.
