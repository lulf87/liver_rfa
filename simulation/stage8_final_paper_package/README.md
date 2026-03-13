# stage8_final_paper_package

Final packaging layer for the liver RFA manuscript.

This stage does **not** rerun the simulation. Instead, it treats the current
`papers/V9/` directory as the authoritative finalized manuscript package and
copies the final figures into a clean `outputs/` directory while validating
that all expected main-text and supplementary figures are present.

## Expected upstream source

By default this package reads from:

```text
../../papers/V9/
```

Expected subdirectories:

```text
papers/V9/figures/main/
papers/V9/figures/supplementary/
papers/V9/figures/preview_png/
```

## What it produces

```text
outputs/
├── fig_main/
├── fig_supp/
├── preview_png/
└── package_manifest.md
```

## Run

```bash
cd ~/Projects/liver_rfa/simulation/stage8_final_paper_package
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash run_all.sh
```
