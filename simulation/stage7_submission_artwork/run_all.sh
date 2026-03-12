#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$PWD/src"
python -m rfa_stage7.cli.package_artwork --config configs/artwork.yaml
