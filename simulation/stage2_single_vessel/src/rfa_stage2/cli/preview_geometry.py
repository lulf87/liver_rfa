#!/usr/bin/env python
from __future__ import annotations
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from rfa_stage2.geometry import build_geometry
from rfa_stage2.io_utils import load_yaml
from rfa_stage2.plotting import plot_geometry

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/base.yaml')
    args = parser.parse_args()
    cfg = load_yaml(ROOT / args.config)
    geom = build_geometry(cfg)
    case_id = cfg['project']['case_id']
    out = ROOT / 'outputs' / 'figures' / f'{case_id}_geometry.png'
    plot_geometry(geom, out, float(cfg['metrics']['safety_margin_mm']))
    print(f'Saved geometry preview to {out}')
if __name__ == '__main__':
    main()
