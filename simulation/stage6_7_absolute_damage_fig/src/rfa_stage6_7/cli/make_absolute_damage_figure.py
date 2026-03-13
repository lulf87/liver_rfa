from __future__ import annotations

import argparse
from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


def load_cfg(path: str | Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def mm_to_inches(mm: float) -> float:
    return mm / 25.4


def canonical_protocol_label(label: str) -> str:
    label_l = str(label).strip().lower()
    if label_l in {"balanced", "moderate", "moderate-energy", "moderate_energy"}:
        return "moderate-energy"
    if label_l in {"aggressive", "high", "high-energy", "high_energy"}:
        return "high-energy"
    return label


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = load_cfg(args.config)
    stage_root = Path(cfg["source"]["final_stage_root"]).resolve()
    csv_path = stage_root / "outputs" / "tables" / "stage4_protocol_gap_diameter_summary.csv"
    outdir = Path("outputs/fig_supp")
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    df["protocol_label"] = df["protocol_label"].map(canonical_protocol_label)

    vessel_diam = float(cfg["selection"]["vessel_diameter_mm"])
    sub = df[np.isclose(df["vessel_diameter_mm"], vessel_diam)].copy()
    if sub.empty:
        raise ValueError(f"No rows found for vessel diameter {vessel_diam} mm in {csv_path}")

    # Derived metrics from existing outputs
    # |A ∩ G| = PPV_target * |A|
    sub["intersection_area_px"] = sub["PPV_target"] * sub["lesion_area_px"]
    sub["abs_overablation_px"] = sub["lesion_area_px"] - sub["intersection_area_px"]
    sub["target_region_coverage"] = sub["intersection_area_px"] / sub["target_area_px"]

    order = [0.0, 2.0, 5.0]
    protocols = ["moderate-energy", "high-energy"]
    colors = {
        "moderate-energy": cfg["figure"]["moderate_color"],
        "high-energy": cfg["figure"]["high_color"],
    }

    width = mm_to_inches(float(cfg["figure"]["width_mm"]))
    height = mm_to_inches(float(cfg["figure"]["height_mm"]))
    fig, axes = plt.subplots(1, 2, figsize=(width, height), constrained_layout=True)
    fig.patch.set_facecolor(cfg["figure"]["bg_color"])

    x = np.arange(len(order))

    # Panel A: absolute overablation outside target
    ax = axes[0]
    for prot in protocols:
        prot_sub = sub[sub["protocol_label"] == prot].set_index("gap_mm").reindex(order)
        ax.plot(x, prot_sub["abs_overablation_px"].values, marker='o', linewidth=1.8,
                color=colors[prot], label=prot)
    ax.set_xticks(x)
    ax.set_xticklabels([str(int(g)) for g in order])
    ax.set_xlabel("Tumor-vessel gap (mm)")
    ax.set_ylabel(r"Absolute overablation outside target $|A \setminus G|$ (px)")
    ax.set_title("(A) Absolute collateral damage", fontsize=10)
    ax.grid(True, alpha=0.25)

    # Panel B: target-region coverage
    ax = axes[1]
    for prot in protocols:
        prot_sub = sub[sub["protocol_label"] == prot].set_index("gap_mm").reindex(order)
        ax.plot(x, prot_sub["target_region_coverage"].values, marker='o', linewidth=1.8,
                color=colors[prot], label=prot)
    ax.set_xticks(x)
    ax.set_xticklabels([str(int(g)) for g in order])
    ax.set_xlabel("Tumor-vessel gap (mm)")
    ax.set_ylabel(r"Target-region coverage $|A \cap G| / |G|$")
    ax.set_title("(B) Target-region coverage", fontsize=10)
    ax.grid(True, alpha=0.25)
    ax.set_ylim(bottom=min(0.6, sub["target_region_coverage"].min() - 0.02), top=1.05)

    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.03))

    for ax in axes:
        ax.set_facecolor(cfg["figure"]["bg_color"])
        for spine in ax.spines.values():
            spine.set_color(cfg["figure"]["axis_color"])
        ax.tick_params(colors=cfg["figure"]["axis_color"])

    out_png = outdir / "FigS7_tradeoff_absolute_damage.png"
    out_pdf = outdir / "FigS7_tradeoff_absolute_damage.pdf"
    fig.savefig(out_png, dpi=int(cfg["figure"]["preview_dpi"]), bbox_inches="tight")
    fig.savefig(out_pdf, dpi=int(cfg["figure"]["publication_dpi"]), bbox_inches="tight")
    print(f"Saved {out_png}")
    print(f"Saved {out_pdf}")


if __name__ == "__main__":
    main()
