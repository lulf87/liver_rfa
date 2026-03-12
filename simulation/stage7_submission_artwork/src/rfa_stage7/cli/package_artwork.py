
from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml
from PIL import Image


@dataclass
class FigureSpec:
    name: str
    source_group: str
    dpi_kind: str


DPI_MAP = {
    "line": (1000, 1000),
    "combo": (600, 600),
    "halftone": (300, 300),
}


def load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def png_to_tiff(src_png: Path, dst_tiff: Path, dpi_kind: str) -> None:
    dpi = DPI_MAP.get(dpi_kind, DPI_MAP["combo"])
    with Image.open(src_png) as im:
        if im.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            alpha = im.getchannel("A") if "A" in im.getbands() else None
            bg.paste(im.convert("RGB"), mask=alpha)
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        ensure_dir(dst_tiff.parent)
        im.save(dst_tiff, format="TIFF", compression="tiff_lzw", dpi=dpi)


def package_group(figure_root: Path, out_root: Path, preview_root: Path, specs: List[FigureSpec]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for spec in specs:
        src_pdf = figure_root / spec.source_group / f"{spec.name}.pdf"
        src_png = preview_root / f"{spec.name}.png"
        out_dir = out_root / spec.source_group
        ensure_dir(out_dir)

        dst_pdf = out_dir / f"{spec.name}.pdf"
        dst_tiff = out_dir / f"{spec.name}.tiff"
        dst_png = out_dir / f"{spec.name}.png"

        if src_pdf.exists():
            shutil.copy2(src_pdf, dst_pdf)
        if src_png.exists():
            shutil.copy2(src_png, dst_png)
            png_to_tiff(src_png, dst_tiff, spec.dpi_kind)

        rows.append(
            {
                "figure": spec.name,
                "group": spec.source_group,
                "src_pdf": str(src_pdf),
                "src_png": str(src_png),
                "dst_pdf": str(dst_pdf),
                "dst_png": str(dst_png),
                "dst_tiff": str(dst_tiff),
                "dpi_kind": spec.dpi_kind,
            }
        )
    return rows


def write_manifest(rows: List[Dict[str, str]], path: Path) -> None:
    lines = [
        "# Submission artwork manifest",
        "",
        "This package contains separate PDF/TIFF/PNG figure files collected from the canonical manuscript figure directories.",
        "",
        "| Figure | Group | DPI class | Source PDF | Source PNG | Output PDF | Output TIFF |",
        "|---|---|---:|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['figure']} | {r['group']} | {r['dpi_kind']} | `{r['src_pdf']}` | `{r['src_png']}` | `{r['dst_pdf']}` | `{r['dst_tiff']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = load_yaml(Path(args.config).resolve())
    stage_root = Path(args.config).resolve().parent.parent
    repo_root = stage_root.parent.parent

    figure_root = (stage_root / cfg["source"]["figure_root"]).resolve()
    preview_root = (stage_root / cfg["source"]["preview_root"]).resolve()
    out_root = (stage_root / cfg["output"]["submission_artwork_root"]).resolve()
    manifest_path = out_root / "manifest" / "submission_artwork_manifest.md"

    specs = [FigureSpec(**x) for x in cfg["figures"]]
    rows = package_group(figure_root, out_root, preview_root, specs)
    ensure_dir(manifest_path.parent)
    write_manifest(rows, manifest_path)

    print(f"Packaged submission artwork to: {out_root}")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
