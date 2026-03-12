#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))

from rfa_stage6_3.refined_benchmark import make_refined_figS4


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/figure_style.yaml')
    args = parser.parse_args()
    make_refined_figS4(args.config, ROOT)
    print('Refined benchmark figure generated.')


if __name__ == '__main__':
    main()
