# stage6_7_absolute_damage_fig

Generate **Fig. S7** from the frozen stage-5 protocol summary table.

## Purpose
This stage adds a supplementary figure that complements `PPV_target` with more direct trade-off descriptors:
- absolute overablation area outside the target region
- target-region coverage ratio `|A ∩ G| / |G|`

## Expected upstream directory
By default, this stage reads:

```text
../stage5_final_frozen/outputs/tables/stage4_protocol_gap_diameter_summary.csv
```

You can change the path in `configs/figure_style.yaml`.

## Outputs
```text
outputs/fig_supp/FigS7_tradeoff_absolute_damage.pdf
outputs/fig_supp/FigS7_tradeoff_absolute_damage.png
```

## Run
```bash
cd ~/Projects/liver_rfa/simulation/stage6_7_absolute_damage_fig
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
bash run_all.sh
```
