# stage6_1_paper_figures

**Status:** current canonical generator for main figures and supplementary Figures S1–S3.

This stage is a **figure-only refinement stage**. It does not rerun the full sweep.

## Outputs produced here

### Main figures
- Fig 1: geometry and metric definition
- Fig 2: representative contour panel
- Fig 3: protocol-dependent MDI maps
- Fig 4: planning trade-off

### Supplementary figures
- Fig S1: convergence
- Fig S2: TCR maps
- Fig S3: VUA maps

## Expected upstream stage

```text
simulation/stage5_final_frozen/
```

If your frozen folder has a different name, edit:

```text
configs/figure_style.yaml
```

## Run

```bash
cd ~/Projects/liver_rfa/simulation/stage6_1_paper_figures
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
bash run_all.sh
```

## Notes

- All quantitative figures use a white publication background.
- Fig. 1 keeps a BioRender-inspired concept-card style.
- TCR and MDI remain the primary quantitative endpoints.
- VUA is retained as a supplementary descriptor.
