from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib import patches
import numpy as np
import pandas as pd

from .io_utils import ensure_dir, load_yaml
from .style import apply_style


class Stage4Bindings:
    def __init__(self, source_stage_root: Path):
        src_root = source_stage_root / "src"
        if str(src_root) not in sys.path:
            sys.path.insert(0, str(src_root))
        from rfa_stage4.geometry import build_geometry
        from rfa_stage4.solver_fd import run_case
        from rfa_stage4.metrics import target_mask_from_tumor
        self.build_geometry = build_geometry
        self.run_case = run_case
        self.target_mask_from_tumor = target_mask_from_tumor


def _resolve_paths(root: Path, cfg: dict) -> dict:
    src = cfg["source"]
    figs = cfg["figures"]
    out = {
        "source_stage_root": (root / src["stage_root"]).resolve(),
        "summary_csv": (root / src["stage_root"] / src["summary_csv"]).resolve(),
        "convergence_csv": (root / src["stage_root"] / src["convergence_csv"]).resolve(),
        "base_config": (root / src["stage_root"] / src["base_config"]).resolve(),
        "protocol_sweep": (root / src["stage_root"] / src["protocol_sweep"]).resolve(),
        "output_main_dir": (root / figs["output_main_dir"]).resolve(),
        "output_supp_dir": (root / figs["output_supp_dir"]).resolve(),
    }
    return out


def _save(fig: plt.Figure, stem: str, out_dir: Path, export_pdf: bool, export_png: bool, png_dpi: int) -> None:
    ensure_dir(out_dir)
    if export_pdf:
        fig.savefig(out_dir / f"{stem}.pdf")
    if export_png:
        fig.savefig(out_dir / f"{stem}.png", dpi=png_dpi)
    plt.close(fig)


def _panel_background(ax, style_cfg: dict) -> None:
    ax.set_facecolor("none")
    bg = patches.FancyBboxPatch(
        (0, 0), 1, 1,
        transform=ax.transAxes,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=0.8,
        edgecolor=style_cfg["panel_edgecolor"],
        facecolor=style_cfg["panel_facecolor"],
        zorder=-10,
        mutation_aspect=1.0,
    )
    ax.add_patch(bg)


def _make_protocol_lookup(sweep_cfg: dict) -> Dict[str, dict]:
    return {p["label"]: p for p in sweep_cfg["protocols"]}


def _rerun_case(bind: Stage4Bindings, base_cfg: dict, protocol_lookup: Dict[str, dict], case_cfg: dict):
    cfg = deepcopy(base_cfg)
    prot = protocol_lookup[case_cfg["protocol_label"]]
    cfg["protocol"]["nominal_power_W"] = float(prot["power_W"])
    cfg["protocol"]["ablation_time_s"] = float(prot["time_s"])
    cfg["geometry"]["disable_vessel"] = not bool(case_cfg["has_vessel"])
    if case_cfg["has_vessel"]:
        cfg["geometry"]["vessel_gap_mm"] = float(case_cfg["gap_mm"])
        cfg["geometry"]["vessel_radius_mm"] = float(case_cfg["vessel_diameter_mm"]) / 2.0
    geom = bind.build_geometry(cfg)
    fields = bind.run_case(geom, cfg)
    target = bind.target_mask_from_tumor(
        geom.tumor_mask,
        float(cfg["metrics"]["safety_margin_mm"]),
        geom.grid.dx_mm,
        geom.grid.dy_mm,
    )
    return cfg, geom, fields, target


def make_fig1(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6))
    for ax in axes:
        _panel_background(ax, style_cfg)

    # (A) Parameterized geometry
    ax = axes[0]
    ax.set_aspect("equal")
    ax.set_xlim(-20, 28)
    ax.set_ylim(-18, 18)
    tumor = patches.Ellipse((0, 0), 15, 15, facecolor=style_cfg["tumor_fill"], alpha=0.45, edgecolor="#333333", linewidth=1.5)
    target = patches.Ellipse((0, 0), 25, 25, fill=False, edgecolor=style_cfg["target_line"], linestyle="--", linewidth=1.5)
    vessel = patches.Circle((14.5, 0), radius=2.5, facecolor=style_cfg["vessel_fill"], edgecolor="#3F6D7A", linewidth=1.2)
    electrode = patches.Rectangle((-0.5, -10), 1.0, 20.0, facecolor=style_cfg["electrode_fill"], alpha=0.9, edgecolor="none")
    ax.add_patch(target); ax.add_patch(tumor); ax.add_patch(vessel); ax.add_patch(electrode)
    ax.annotate("", xy=(7.5, -6.5), xytext=(12.0, -6.5), arrowprops=dict(arrowstyle="<->", color=style_cfg["accent_color"], lw=1.2))
    ax.text(9.75, -8.2, "gap", ha="center", va="top", color=style_cfg["accent_color"])
    ax.annotate("", xy=(17.0, -2.5), xytext=(17.0, 2.5), arrowprops=dict(arrowstyle="<->", color="#3F6D7A", lw=1.2))
    ax.text(18.2, 0.0, "diameter", rotation=90, va="center", color="#3F6D7A")
    ax.text(0.02, 1.04, "(A) Parameterized geometry", transform=ax.transAxes, fontweight="bold")
    ax.text(-9.2, 8.6, "tumor")
    ax.text(-14.8, 13.2, "target margin")
    ax.text(-2.6, -12.5, "electrode")
    ax.text(11.1, 5.6, "vessel")
    ax.axis("off")

    # (B) Margin deficit and vessel-side undercoverage
    ax = axes[1]
    ax.set_aspect("equal")
    ax.set_xlim(-20, 24)
    ax.set_ylim(-18, 18)
    tumor = patches.Ellipse((0, 0), 15, 15, facecolor=style_cfg["tumor_fill"], alpha=0.45, edgecolor="#333333", linewidth=1.5)
    target = patches.Ellipse((0, 0), 25, 25, fill=False, edgecolor=style_cfg["target_line"], linestyle="--", linewidth=1.5)
    vessel = patches.Circle((14.5, 0), radius=2.5, facecolor=style_cfg["vessel_fill"], edgecolor="#3F6D7A", linewidth=1.2)
    lesion = patches.PathPatch(
        patches.Path(
            [(-12, -2), (-12, 9), (-8, 14), (0, 15), (8, 14), (10, 9), (9.5, 2),
             (6.0, 0.5), (9.5, -2), (10, -9), (8, -14), (0, -15), (-8, -14), (-12, -9), (-12, -2)],
            [1] + [2]*13 + [79]
        ),
        fill=False, edgecolor=style_cfg["lesion_line"], linewidth=2.0
    )
    ax.add_patch(target); ax.add_patch(tumor); ax.add_patch(vessel); ax.add_patch(lesion)
    wedge = patches.Wedge((0, 0), 8.7, -23, 23, width=1.5, facecolor="#FFD6A5", edgecolor="#FF922B", alpha=0.9)
    ax.add_patch(wedge)
    ax.text(0.02, 1.04, "(B) Shape-based endpoints", transform=ax.transAxes, fontweight="bold")
    ax.text(-16.0, 12.0, "dashed: desired\n5-mm margin", fontsize=7)
    ax.text(-15.8, -13.8, "purple: predicted lesion", fontsize=7, color=style_cfg["lesion_line"])
    ax.annotate("vessel-side\nundercoverage", xy=(7.2, 0), xytext=(12.0, 9.0),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="#FF922B"),
                color="#C25B00", fontsize=7)
    ax.text(-15.8, -3.0, "MDI: fraction of tumor\nboundary with local margin < 5 mm", fontsize=7)
    ax.axis("off")

    # (C) Planning workflow card
    ax = axes[2]
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.02, 1.04, "(C) Planning outputs", transform=ax.transAxes, fontweight="bold")
    box1 = patches.FancyBboxPatch((0.06, 0.60), 0.24, 0.24, boxstyle="round,pad=0.03,rounding_size=0.04",
                                  facecolor="#EDF6F9", edgecolor="#B5CDD5")
    box2 = patches.FancyBboxPatch((0.38, 0.52), 0.24, 0.32, boxstyle="round,pad=0.03,rounding_size=0.04",
                                  facecolor="#FFF7E8", edgecolor="#E5C891")
    box3 = patches.FancyBboxPatch((0.70, 0.60), 0.24, 0.24, boxstyle="round,pad=0.03,rounding_size=0.04",
                                  facecolor="#F3F0FF", edgecolor="#D0C5FF")
    for b in (box1, box2, box3):
        ax.add_patch(b)
    ax.text(0.18, 0.79, "Inputs", ha="center", fontweight="bold")
    ax.text(0.18, 0.70, "gap\nvessel size\nprotocol", ha="center")
    ax.text(0.50, 0.79, "2D reduced-order\nmodel", ha="center", fontweight="bold")
    ax.text(0.50, 0.66, "electrical\nthermal\ndamage", ha="center")
    ax.text(0.82, 0.79, "Outputs", ha="center", fontweight="bold")
    ax.text(0.82, 0.70, "TCR\nMDI\nPPV_target", ha="center")
    ax.annotate("", xy=(0.38, 0.72), xytext=(0.30, 0.72), arrowprops=dict(arrowstyle="->", lw=1.4, color=style_cfg["accent_color"]))
    ax.annotate("", xy=(0.70, 0.72), xytext=(0.62, 0.72), arrowprops=dict(arrowstyle="->", lw=1.4, color=style_cfg["accent_color"]))
    ax.text(0.06, 0.18,
            "Primary endpoints:\n• TCR (tumor coverage)\n• MDI (margin deficit)\n\nSupplementary:\n• PPV_target\n• VUA",
            va="top")
    fig.subplots_adjust(wspace=0.18)
    _save(fig, "Fig1_geometry_metric_definition", paths["output_main_dir"], cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def _draw_case_contour(ax, geom, fields, target_mask, panel_label, short_label, style_cfg):
    _panel_background(ax, style_cfg)
    ax.contourf(geom.xx_mm, geom.yy_mm, geom.tumor_mask.astype(float), levels=[0.5, 1.5], colors=[style_cfg["tumor_fill"]], alpha=0.35)
    if geom.vessel_mask.any():
        ax.contourf(geom.xx_mm, geom.yy_mm, geom.vessel_mask.astype(float), levels=[0.5, 1.5], colors=[style_cfg["vessel_fill"]], alpha=0.85)
    ax.contourf(geom.xx_mm, geom.yy_mm, geom.electrode_mask.astype(float), levels=[0.5, 1.5], colors=[style_cfg["electrode_fill"]], alpha=0.9)
    ax.contour(geom.xx_mm, geom.yy_mm, geom.tumor_mask.astype(float), levels=[0.5], colors="#333333", linewidths=1.3)
    ax.contour(geom.xx_mm, geom.yy_mm, target_mask.astype(float), levels=[0.5], colors=style_cfg["target_line"], linewidths=1.2, linestyles="--")
    ax.contour(geom.xx_mm, geom.yy_mm, fields["lesion_mask"].astype(float), levels=[0.5], colors=style_cfg["lesion_line"], linewidths=1.8)
    ax.set_aspect("equal")
    ax.set_xlim(geom.grid.x_mm.min(), geom.grid.x_mm.max())
    ax.set_ylim(geom.grid.y_mm.min(), geom.grid.y_mm.max())
    ax.set_xticks([-20, 0, 20]); ax.set_yticks([-20, 0, 20])
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.text(0.02, 1.03, f"{panel_label} {short_label}", transform=ax.transAxes, fontweight="bold")


def make_fig2(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    base_cfg = load_yaml(paths["base_config"])
    sweep_cfg = load_yaml(paths["protocol_sweep"])
    prot_lookup = _make_protocol_lookup(sweep_cfg)
    bind = Stage4Bindings(paths["source_stage_root"])

    fig, axes = plt.subplots(2, 2, figsize=(8.2, 7.2))
    for ax, case_cfg in zip(axes.ravel(), cfg["representative_cases"]):
        _, geom, fields, target = _rerun_case(bind, base_cfg, prot_lookup, case_cfg)
        _draw_case_contour(ax, geom, fields, target, case_cfg["panel_label"], case_cfg["short_label"], style_cfg)

    handles = [
        patches.Patch(facecolor=style_cfg["tumor_fill"], alpha=0.35, label="Tumor"),
        plt.Line2D([0], [0], color=style_cfg["target_line"], linestyle="--", lw=1.2, label="Target margin"),
        patches.Patch(facecolor=style_cfg["vessel_fill"], alpha=0.85, label="Vessel"),
        patches.Patch(facecolor=style_cfg["electrode_fill"], alpha=0.9, label="Electrode"),
        plt.Line2D([0], [0], color=style_cfg["lesion_line"], lw=1.8, label="Predicted lesion"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(hspace=0.28, wspace=0.18, bottom=0.14)
    _save(fig, "Fig2_representative_contours", paths["output_main_dir"], cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def _heat(ax, data, gaps, diameters, cmap, vmin=None, vmax=None, annotate=True):
    im = ax.imshow(data, origin="lower", aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(np.arange(len(gaps))); ax.set_xticklabels([f"{g:g}" for g in gaps])
    ax.set_yticks(np.arange(len(diameters))); ax.set_yticklabels([f"{d:g}" for d in diameters])
    ax.set_xlabel("Vessel gap (mm)")
    ax.set_ylabel("Vessel diameter (mm)")
    if annotate:
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                ax.text(j, i, f"{data[i,j]:.3f}".rstrip("0").rstrip("."), ha="center", va="center", fontsize=7)
    return im


def _metric_matrix(df: pd.DataFrame, protocol: str, metric: str, gaps: List[float], diameters: List[float]) -> np.ndarray:
    arr = np.zeros((len(diameters), len(gaps)), dtype=float)
    sub = df[(df["protocol_label"] == protocol) & (df["has_vessel"] == 1)]
    for i, d in enumerate(diameters):
        for j, g in enumerate(gaps):
            row = sub[(np.isclose(sub["vessel_diameter_mm"], d)) & (np.isclose(sub["gap_mm"], g))].iloc[0]
            arr[i, j] = float(row[metric])
    return arr


def make_fig3(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    summary = pd.read_csv(paths["summary_csv"])
    sweep_cfg = load_yaml(paths["protocol_sweep"])
    protocols = [p["label"] for p in sweep_cfg["protocols"]]
    if protocols[:2] != ["balanced", "aggressive"] and len(protocols) >= 2:
        balanced, aggressive = protocols[0], protocols[1]
    else:
        balanced, aggressive = "balanced", "aggressive"
    gaps = [float(v) for v in sweep_cfg["grid"]["gaps_mm"]]
    diameters = [float(v) for v in sweep_cfg["grid"]["vessel_diameters_mm"]]

    m_bal = _metric_matrix(summary, balanced, "MDI", gaps, diameters)
    m_agg = _metric_matrix(summary, aggressive, "MDI", gaps, diameters)
    delta = m_bal - m_agg
    vmin = float(min(m_bal.min(), m_agg.min()))
    vmax = float(max(m_bal.max(), m_agg.max()))
    dmax = float(np.max(np.abs(delta)))

    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.8), gridspec_kw={"width_ratios": [1, 1, 1.05]})
    for ax in axes:
        _panel_background(ax, style_cfg)

    im1 = _heat(axes[0], m_bal, gaps, diameters, cmap="viridis", vmin=vmin, vmax=vmax)
    axes[0].text(0.02, 1.04, "(A) Balanced", transform=axes[0].transAxes, fontweight="bold")
    im2 = _heat(axes[1], m_agg, gaps, diameters, cmap="viridis", vmin=vmin, vmax=vmax)
    axes[1].text(0.02, 1.04, "(B) Aggressive", transform=axes[1].transAxes, fontweight="bold")
    im3 = _heat(axes[2], delta, gaps, diameters, cmap="coolwarm", vmin=-dmax, vmax=dmax)
    axes[2].text(0.02, 1.04, "(C) ΔMDI (Balanced − Aggressive)", transform=axes[2].transAxes, fontweight="bold")

    cbar1 = fig.colorbar(im1, ax=axes[:2], fraction=0.03, pad=0.03)
    cbar1.set_label("MDI")
    cbar2 = fig.colorbar(im3, ax=axes[2], fraction=0.046, pad=0.04)
    cbar2.set_label("ΔMDI")
    fig.subplots_adjust(wspace=0.28)
    _save(fig, "Fig3_protocol_MDI_maps", paths["output_main_dir"], cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def _line_panel(ax, df: pd.DataFrame, metric: str, d_ref: float, style_cfg: dict):
    _panel_background(ax, style_cfg)
    for label, color in [("balanced", style_cfg["balanced_color"]), ("aggressive", style_cfg["aggressive_color"])]:
        sub = df[(df["protocol_label"] == label) & (df["has_vessel"] == 1) & (np.isclose(df["vessel_diameter_mm"], d_ref))]
        sub = sub.sort_values("gap_mm")
        ax.plot(sub["gap_mm"], sub[metric], marker="o", color=color, linewidth=2.0, label=label.capitalize())
    ax.set_xlabel("Vessel gap (mm)")
    ax.set_ylabel(metric)
    ax.legend(frameon=False, loc="best")


def make_fig4(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    summary = pd.read_csv(paths["summary_csv"])
    d_ref = float(cfg["tradeoff"]["vessel_diameter_mm"])

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.6))
    _line_panel(axes[0], summary, "MDI", d_ref, style_cfg)
    axes[0].text(0.02, 1.04, "(A) Margin deficit", transform=axes[0].transAxes, fontweight="bold")
    _line_panel(axes[1], summary, "PPV_target", d_ref, style_cfg)
    axes[1].text(0.02, 1.04, "(B) Target specificity", transform=axes[1].transAxes, fontweight="bold")
    fig.subplots_adjust(wspace=0.26)
    _save(fig, "Fig4_tradeoff_MDI_PPV", paths["output_main_dir"], cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def make_figS1(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    conv = pd.read_csv(paths["convergence_csv"])
    severe = conv[conv["case_label"] == "severe_vessel"].copy()
    grid = severe[severe["group"] == "grid"].sort_values("grid_n")
    dt = severe[severe["group"] == "dt"].sort_values("dt_s", ascending=False)

    fig, axes = plt.subplots(2, 2, figsize=(8.2, 6.2))
    for ax in axes.ravel():
        _panel_background(ax, style_cfg)

    axes[0,0].plot(grid["grid_n"], grid["TCR"], marker="o", color=style_cfg["balanced_color"])
    axes[0,0].set_xlabel("Grid size (n × n)"); axes[0,0].set_ylabel("TCR")
    axes[0,0].text(0.02, 1.04, "(A) Severe-vessel grid convergence: TCR", transform=axes[0,0].transAxes, fontweight="bold")

    axes[0,1].plot(grid["grid_n"], grid["MDI"], marker="o", color=style_cfg["aggressive_color"])
    axes[0,1].set_xlabel("Grid size (n × n)"); axes[0,1].set_ylabel("MDI")
    axes[0,1].text(0.02, 1.04, "(B) Severe-vessel grid convergence: MDI", transform=axes[0,1].transAxes, fontweight="bold")

    axes[1,0].plot(dt["dt_s"], dt["TCR"], marker="o", color=style_cfg["balanced_color"])
    axes[1,0].set_xlabel("Time step (s)"); axes[1,0].set_ylabel("TCR")
    axes[1,0].invert_xaxis()
    axes[1,0].text(0.02, 1.04, "(C) Severe-vessel time-step check: TCR", transform=axes[1,0].transAxes, fontweight="bold")

    axes[1,1].plot(dt["dt_s"], dt["MDI"], marker="o", color=style_cfg["aggressive_color"])
    axes[1,1].set_xlabel("Time step (s)"); axes[1,1].set_ylabel("MDI")
    axes[1,1].invert_xaxis()
    axes[1,1].text(0.02, 1.04, "(D) Severe-vessel time-step check: MDI", transform=axes[1,1].transAxes, fontweight="bold")

    fig.subplots_adjust(hspace=0.34, wspace=0.28)
    _save(fig, "FigS1_convergence", paths["output_supp_dir"], cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def make_figS2_S3(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    summary = pd.read_csv(paths["summary_csv"])
    sweep_cfg = load_yaml(paths["protocol_sweep"])
    gaps = [float(v) for v in sweep_cfg["grid"]["gaps_mm"]]
    diameters = [float(v) for v in sweep_cfg["grid"]["vessel_diameters_mm"]]

    for metric, stem, cbar in [("TCR", "FigS2_TCR_maps", "TCR"), ("VUA_deg", "FigS3_VUA_maps", "VUA (deg)")]:
        if metric == "TCR":
            vmin = float(summary.loc[summary["has_vessel"] == 1, metric].min())
            vmax = 1.0
            cmap = "viridis"
        else:
            vmin = 0.0
            vmax = float(summary.loc[summary["has_vessel"] == 1, metric].max())
            cmap = "magma"
        fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.6))
        mats = []
        for prot in ["balanced", "aggressive"]:
            mats.append(_metric_matrix(summary, prot, metric, gaps, diameters))
        for ax, mat, prot, label in zip(axes, mats, ["balanced","aggressive"], ["(A) Balanced", "(B) Aggressive"]):
            _panel_background(ax, style_cfg)
            im = _heat(ax, mat, gaps, diameters, cmap=cmap, vmin=vmin, vmax=vmax)
            ax.text(0.02, 1.04, label, transform=ax.transAxes, fontweight="bold")
        cbar_obj = fig.colorbar(im, ax=axes, fraction=0.04, pad=0.03)
        cbar_obj.set_label(cbar)
        fig.subplots_adjust(wspace=0.22)
        _save(fig, stem, paths["output_supp_dir"], cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def make_all(config_path: str | Path, root: Path) -> None:
    cfg = load_yaml(root / config_path)
    paths = _resolve_paths(root, cfg)
    make_fig1(cfg, paths)
    make_fig2(cfg, paths)
    make_fig3(cfg, paths)
    make_fig4(cfg, paths)
    make_figS1(cfg, paths)
    make_figS2_S3(cfg, paths)
