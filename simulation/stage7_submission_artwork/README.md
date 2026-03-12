# stage7_submission_artwork

This stage does **not** rerun any simulation. It packages the canonical manuscript figures into separate submission-ready artwork files.

## Inputs

This stage reads from the canonical figure locations:

```text
manuscript/figures/main/
manuscript/figures/supplementary/
manuscript/figures/preview_png/
```

## Outputs

The packaged artwork is written to:

```text
manuscript/figures/submission_artwork/
  main/
  supplementary/
  manifest/
```

For each figure, this stage will:

- copy the canonical PDF file
- copy the preview PNG file
- generate a TIFF file from the preview PNG using LZW compression
- write a submission-artwork manifest

## DPI policy

The stage uses a figure-class policy:

- `line` → 1000 dpi TIFF
- `combo` → 600 dpi TIFF
- `halftone` → 300 dpi TIFF

The authoritative vector files remain the PDF copies.

## Run

```bash
cd ~/Projects/liver_rfa/simulation/stage7_submission_artwork
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
bash run_all.sh
```
