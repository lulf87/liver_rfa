# stage6_4_shape_vs_size_fig

Generate **Fig. S6**: lesion size versus shape-based margin deficit.

## Default inputs
- `../stage5_final_frozen/outputs/tables/stage4_protocol_gap_diameter_summary.csv`

## Outputs
- `outputs/fig_supp/FigS6_shape_vs_size_comparison.pdf`
- `outputs/fig_supp/FigS6_shape_vs_size_comparison.png`

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
bash run_all.sh
```
