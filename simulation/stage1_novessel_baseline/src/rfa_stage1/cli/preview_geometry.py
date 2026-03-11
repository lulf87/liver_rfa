#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from rfa_stage1.geometry import build_geometry
from rfa_stage1.io_utils import load_yaml
from rfa_stage1.plotting import plot_geometry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/base.yaml")
    args = parser.parse_args()

    cfg = load_yaml(ROOT / args.config)
    geom = build_geometry(cfg)
    case_id = cfg["project"]["case_id"]
    output_path = ROOT / "outputs" / "figures" / f"{case_id}_geometry.png"
    plot_geometry(geom, output_path, float(cfg["metrics"]["safety_margin_mm"]))
    print(f"Saved geometry preview to {output_path}")


if __name__ == "__main__":
    main()
