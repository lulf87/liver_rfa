#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIG_DIR="${ROOT_DIR}/manuscript/figures"
ARCHIVE_DIR="${FIG_DIR}/archive_legacy_root"

mkdir -p "${ARCHIVE_DIR}"

shopt -s nullglob
for f in "${FIG_DIR}"/Fig*.pdf "${FIG_DIR}"/Fig*.png "${FIG_DIR}"/Fig*.tif "${FIG_DIR}"/Fig*.tiff; do
  if [[ -f "$f" ]]; then
    mv "$f" "${ARCHIVE_DIR}/"
    echo "Moved $(basename "$f") -> manuscript/figures/archive_legacy_root/"
  fi
done

echo "Done."
