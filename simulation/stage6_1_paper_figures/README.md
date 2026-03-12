
# stage6_1_paper_figures

This is a **figure-only refinement stage**. It does not rerun the full sweep.  
It reads the frozen outputs from `../stage5_final_frozen/` and rebuilds the
paper figures with a more journal-ready style:

Main figures
- Fig 1: geometry and metric definition (BioRender-inspired concept layout)
- Fig 2: representative contour panel (white background, tighter crop, smoother contours)
- Fig 3: protocol-dependent MDI maps (shared colorbar + MDI reduction panel)
- Fig 4: planning trade-off (shared legend)

Supplementary
- Fig S1: convergence
- Fig S2: TCR maps
- Fig S3: VUA maps

## Expected upstream stage
By default this stage expects:

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
- All quantitative figures use a **white publication background**.
- Fig. 1 keeps a **BioRender-inspired concept card** style.
- TCR and MDI remain the primary quantitative endpoints.
- VUA is kept as a supplementary descriptor.
