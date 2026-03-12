# stage6_2_supplementary_figures

**Status:** current canonical generator for Supplementary Figure S5.

This stage adds the protocol-selection supplementary figure needed to justify the final balanced and aggressive protocol choices.

## Output produced here

- **Fig S5:** protocol selection under the no-vessel baseline
  - (A) TCR heatmap across power/time
  - (B) MDI heatmap across power/time
  - marks the final **Balanced** and **Aggressive** protocols

## Expected upstream stages

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
