from __future__ import annotations
import argparse
from pathlib import Path
from stage8_final.packager import make_all


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/package.yaml')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    make_all(args.config, root)


if __name__ == '__main__':
    main()
