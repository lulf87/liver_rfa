# stage6_3_benchmark_patch

This patch refines **Fig S4(B)** so that the benchmark is easier to interpret in the paper.

Instead of plotting the **absolute lesion-diameter penalty (mm)**, the updated figure uses:

```text
normalized lesion reduction (%)
= (D_no_vessel - D_vessel) / D_no_vessel × 100
```

This makes the balanced and aggressive protocols directly comparable even when their no-vessel baseline diameters differ.

## Expected upstream stage
By default this patch expects:

```text
simulation/stage5_final_frozen/
```

If your folder name differs, edit:

```text
configs/figure_style.yaml
```

## Run
```bash
cd ~/Projects/liver_rfa/simulation/stage6_3_benchmark_patch
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
```
