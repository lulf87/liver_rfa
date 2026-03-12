# stage6_3_benchmark_patch

**Status:** current canonical generator for Supplementary Figure S4.

This patch refines the benchmark figure so that the paper package uses a more interpretable normalized benchmark.

## Output produced here

- **Fig S4:** calibration and normalized heat-sink benchmark
  - (A) baseline calibration curve
  - (B) normalized lesion reduction (%) benchmark

## Expected upstream stage

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
