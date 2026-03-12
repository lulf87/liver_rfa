
# stage6_2_supplementary_figures

This stage adds the two missing supplementary figures that strengthen the paper package:

- **Fig S4:** Calibration and internal benchmark
  - (A) no-vessel calibration sweep of `source_scale_per_W` against equivalent lesion diameter
  - (B) lesion-diameter penalty versus vessel gap as an internal heat-sink benchmark

- **Fig S5:** Protocol selection under the no-vessel baseline
  - (A) TCR heatmap across power/time
  - (B) MDI heatmap across power/time
  - marks the final **Balanced** and **Aggressive** protocols

## Expected upstream stages
By default this stage expects:

```text
simulation/stage5_final_frozen/
simulation/stage1_novessel_baseline/
```

If your folder names differ, edit:

```text
configs/figure_style.yaml
```

## Run

```bash
cd ~/Projects/liver_rfa/simulation/stage6_2_supplementary_figures
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
bash run_all.sh
```

## Outputs

```text
outputs/fig_supp/FigS4_calibration_benchmark.pdf
outputs/fig_supp/FigS4_calibration_benchmark.png
outputs/fig_supp/FigS5_protocol_selection.pdf
outputs/fig_supp/FigS5_protocol_selection.png
```
