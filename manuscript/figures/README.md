# Manuscript figures

This directory contains the canonical figure files used by the manuscript.

## Canonical subdirectories

- `main/` — final main-text figure PDFs
- `supplementary/` — final supplementary figure PDFs
- `preview_png/` — preview PNG copies for drafting and quick inspection
- `manifest/` — provenance and packaging manifest
- `archive_legacy_root/` — optional parking area for loose historical files previously kept at the root of `manuscript/figures/`

## Policy

For manuscript assembly and submission, use only:

- `main/*.pdf`
- `supplementary/*.pdf`

Do not cite per-stage outputs directly in the manuscript.

## Packaging for submission

Use:

```bash
cd simulation/stage7_submission_artwork
bash run_all.sh
```

This will create a separate `submission_artwork/` package containing individual PDF and TIFF files for journal submission.
