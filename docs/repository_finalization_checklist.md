# Repository finalization checklist

This note captures the final repository-polishing tasks that are not part of the numerical study itself.

## Already addressed by this patch

- Added a top-level `README.md`
- Reformatted `manuscript/figures/manifest/figure_manifest.md`
- Added status-oriented READMEs for stage 6 figure-generation stages
- Added a cleanup script for legacy loose figure files under `manuscript/figures/`
- Added `stage7_submission_artwork/` for packaging separate PDF/TIFF figure files

## Manual GitHub settings still recommended

These items must be set in the GitHub web interface and cannot be committed through ordinary repository files:

1. Add a short repository description, for example:
   `Reduced-order heat-sink-aware planning model for perivascular liver RFA with shape-based endpoints`

2. Add repository topics, for example:
   `radiofrequency-ablation`, `liver`, `heat-sink`, `in-silico`, `finite-difference`, `biomedical-engineering`

3. Create a GitHub Release, for example:
   `submission-artifacts-v1`

4. Optionally attach:
   - `stage5_final_frozen_*.tar.gz`
   - manuscript figure PDFs
   - final tables

## Canonical figure policy

Use these as the canonical final figure locations:

- `manuscript/figures/main/*.pdf`
- `manuscript/figures/supplementary/*.pdf`

Use these only for preview and drafting:

- `manuscript/figures/preview_png/*.png`

## Legacy figure cleanup

If loose root-level files remain under `manuscript/figures/`, run:

```bash
bash docs/repo_tools/cleanup_legacy_figure_files.sh
```

This will move loose `Fig*.pdf/png/tif/tiff` files from `manuscript/figures/` into:

```text
manuscript/figures/archive_legacy_root/
```
