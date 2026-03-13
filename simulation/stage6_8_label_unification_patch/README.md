# stage6_8_label_unification_patch

This patch harmonizes figure-internal protocol labels from:
- Balanced -> Moderate-energy
- Aggressive -> High-energy

It updates the plotting code used by:
- stage6_1_paper_figures
- stage6_2_supplementary_figures
- stage6_4_shape_vs_size_fig

## Where to place this patch

Put this directory under:

simulation/stage6_8_label_unification_patch/

## How to apply

From the repository root:

```bash
cd ~/Projects/liver_rfa/simulation/stage6_8_label_unification_patch
bash apply_patch.sh
```

After applying the patch, regenerate the affected figures from the original stage directories.
