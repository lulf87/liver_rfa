#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$PWD/src"
python -m stage8_final.cli.package_final --config configs/package.yaml
