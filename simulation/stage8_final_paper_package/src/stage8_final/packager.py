from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import yaml


@dataclass
class Config:
    papers_v9_root: Path
    expected_main: list[str]
    expected_supp: list[str]
    expected_preview: list[str]


def load_config(config_path: Path) -> Config:
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    base = config_path.parent.parent.resolve()
    papers_v9_root = (base / cfg['source']['papers_v9_root']).resolve()
    return Config(
        papers_v9_root=papers_v9_root,
        expected_main=list(cfg['expected']['main']),
        expected_supp=list(cfg['expected']['supplementary']),
        expected_preview=list(cfg['expected']['preview_png']),
    )


def ensure_sources(cfg: Config) -> tuple[Path, Path, Path]:
    main_dir = cfg.papers_v9_root / 'figures' / 'main'
    supp_dir = cfg.papers_v9_root / 'figures' / 'supplementary'
    prev_dir = cfg.papers_v9_root / 'figures' / 'preview_png'
    for p in (main_dir, supp_dir, prev_dir):
        if not p.exists():
            raise FileNotFoundError(f'Missing source directory: {p}')
    return main_dir, supp_dir, prev_dir


def validate_files(src_dir: Path, required: list[str]) -> None:
    missing = [name for name in required if not (src_dir / name).exists()]
    if missing:
        joined = ', '.join(missing)
        raise FileNotFoundError(f'Missing required files in {src_dir}: {joined}')


def copy_group(src_dir: Path, dst_dir: Path, files: list[str]) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in files:
        shutil.copy2(src_dir / name, dst_dir / name)


def write_manifest(out_root: Path, cfg: Config) -> None:
    text = f'''# stage8 final paper package\n\nSource papers/V9 root: {cfg.papers_v9_root}\n\n## Main figures\n'''
    for name in cfg.expected_main:
        text += f'- figures/main/{name}\n'
    text += '\n## Supplementary figures\n'
    for name in cfg.expected_supp:
        text += f'- figures/supplementary/{name}\n'
    text += '\n## Preview PNG\n'
    for name in cfg.expected_preview:
        text += f'- figures/preview_png/{name}\n'
    (out_root / 'package_manifest.md').write_text(text, encoding='utf-8')


def make_all(config_path: str | Path, root: str | Path) -> None:
    root = Path(root).resolve()
    cfg = load_config(Path(config_path).resolve())
    main_src, supp_src, prev_src = ensure_sources(cfg)
    validate_files(main_src, cfg.expected_main)
    validate_files(supp_src, cfg.expected_supp)
    validate_files(prev_src, cfg.expected_preview)
    out_root = root / 'outputs'
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    copy_group(main_src, out_root / 'fig_main', cfg.expected_main)
    copy_group(supp_src, out_root / 'fig_supp', cfg.expected_supp)
    copy_group(prev_src, out_root / 'preview_png', cfg.expected_preview)
    write_manifest(out_root, cfg)
    print(f'Packaged final figures into {out_root}')
