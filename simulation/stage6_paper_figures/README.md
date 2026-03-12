# stage6_paper_figures

This stage does **not** solve the full sweep again. It reads the frozen results from
`../stage5_final_frozen/` and rebuilds a **CMPB-compatible, BioRender-inspired** figure set:

Main figures
- Fig 1: geometry and metric definition
- Fig 2: representative contour panel
- Fig 3: protocol-dependent MDI maps
- Fig 4: planning trade-off curves

Supplementary figures
- Fig S1: convergence summary
- Fig S2: TCR maps
- Fig S3: VUA maps

## Expected upstream stage
By default this stage expects the frozen source stage here:

```text
simulation/stage5_final_frozen/
```

If your frozen directory has a different name, edit `configs/figure_style.yaml`.

## How to run

```bash
cd ~/Projects/liver_rfa/simulation/stage6_paper_figures
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
bash run_all.sh
```

## Output
Main figures will be written to:

```text
outputs/fig_main/
```

Supplementary figures will be written to:

```text
outputs/fig_supp/
```

Each figure is exported as both:
- PDF (vector-friendly for manuscript assembly)
- PNG (600 dpi)

## Notes
1. Fig 2 is regenerated from the frozen `base.yaml` and protocol definitions by rerunning only a **small set of representative cases** for plotting.
2. The final manuscript should keep **TCR** and **MDI** as primary quantitative endpoints.
3. `VUA` is exported as a supplementary descriptor because it remains more grid-sensitive.
