
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Dict, List, Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib import cm, colors, patches
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

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
    return {
        "source_stage_root": (root / src["stage_root"]).resolve(),
        "summary_csv": (root / src["stage_root"] / src["summary_csv"]).resolve(),
        "convergence_csv": (root / src["stage_root"] / src["convergence_csv"]).resolve(),
        "base_config": (root / src["stage_root"] / src["base_config"]).resolve(),
        "protocol_sweep": (root / src["stage_root"] / src["protocol_sweep"]).resolve(),
        "output_main_dir": ensure_dir((root / figs["output_main_dir"]).resolve()),
        "output_supp_dir": ensure_dir((root / figs["output_supp_dir"]).resolve()),
    }


def _save(fig: plt.Figure, stem: str, out_dir: Path, export_pdf: bool, export_png: bool, png_dpi: int) -> None:
    ensure_dir(out_dir)
    if export_pdf:
        fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.02)
    if export_png:
        fig.savefig(out_dir / f"{stem}.png", dpi=png_dpi, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def _concept_panel(ax, style_cfg: dict) -> None:
    ax.set_facecolor("none")
    card = patches.FancyBboxPatch(
        (0, 0), 1, 1,
        transform=ax.transAxes,
        boxstyle="round,pad=0.018,rounding_size=0.03",
        linewidth=0.8,
        edgecolor=style_cfg["concept_panel_edgecolor"],
        facecolor=style_cfg["concept_panel_facecolor"],
        zorder=-10,
    )
    ax.add_patch(card)


def _data_axis(ax, style_cfg: dict) -> None:
    ax.set_facecolor("white")
    ax.spines["left"].set_color(style_cfg["axis_color"])
    ax.spines["bottom"].set_color(style_cfg["axis_color"])
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)


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


def _text_color_for_value(value: float, cmap_name: str, vmin: float, vmax: float) -> str:
    if vmax <= vmin:
        return "#222222"
    cmap = cm.get_cmap(cmap_name)
    norm = colors.Normalize(vmin=vmin, vmax=vmax)
    r, g, b, _ = cmap(norm(value))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "white" if luminance < 0.42 else "#2F2F2F"


def _annotate_heatmap(ax, data: np.ndarray, cmap_name: str, vmin: float, vmax: float, fmt: str = ".3f") -> None:
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = float(data[i, j])
            if fmt == "int":
                s = f"{int(round(val))}"
            else:
                s = f"{val:{fmt}}".rstrip("0").rstrip(".")
            ax.text(j, i, s, ha="center", va="center",
                    fontsize=8.2, color=_text_color_for_value(val, cmap_name, vmin, vmax))


def _heat(ax, data, gaps, diameters, cmap, vmin=None, vmax=None, annotate=True, ylabel=True, xlabel=True):
    im = ax.imshow(data, origin="lower", aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(np.arange(len(gaps))); ax.set_xticklabels([f"{g:g}" for g in gaps])
    ax.set_yticks(np.arange(len(diameters))); ax.set_yticklabels([f"{d:g}" for d in diameters])
    if xlabel:
        ax.set_xlabel("Vessel gap (mm)")
    else:
        ax.set_xlabel("")
    if ylabel:
        ax.set_ylabel("Vessel diameter (mm)")
    else:
        ax.set_ylabel("")
    if annotate:
        _annotate_heatmap(ax, data, cmap, vmin if vmin is not None else np.min(data), vmax if vmax is not None else np.max(data))
    return im


def _smooth_mask(mask: np.ndarray, sigma: float = 0.8) -> np.ndarray:
    return gaussian_filter(mask.astype(float), sigma=sigma)


def _add_scale_bar(ax, length_mm: float, x0: float, y0: float, style_cfg: dict) -> None:
    ax.plot([x0, x0 + length_mm], [y0, y0], color=style_cfg["axis_color"], lw=2.2, solid_capstyle="butt")
    ax.text(x0 + length_mm / 2, y0 - 2.2, f"{int(length_mm)} mm", ha="center", va="top", fontsize=7.5)


def _case_limits() -> Tuple[Tuple[float, float], Tuple[float, float]]:
    return (-24.0, 24.0), (-24.0, 24.0)


def _draw_contour_case(ax, geom, fields, target_mask, panel_label, short_label, style_cfg,
                       show_xlabel: bool, show_ylabel: bool, add_scale_bar: bool = False):
    _data_axis(ax, style_cfg)
    ax.set_aspect("equal")

    xx, yy = geom.xx_mm, geom.yy_mm
    tumor = _smooth_mask(geom.tumor_mask, sigma=0.6)
    vessel = _smooth_mask(geom.vessel_mask, sigma=0.6) if geom.vessel_mask.any() else None
    target = _smooth_mask(target_mask, sigma=0.7)
    lesion = _smooth_mask(fields["lesion_mask"], sigma=0.8)

    ax.contourf(xx, yy, tumor, levels=[0.5, 2.0], colors=[style_cfg["tumor_fill"]], alpha=0.35, zorder=1)
    if vessel is not None:
        ax.contourf(xx, yy, vessel, levels=[0.5, 2.0], colors=[style_cfg["vessel_fill"]], alpha=0.95, zorder=2)
    ax.contourf(xx, yy, geom.electrode_mask.astype(float), levels=[0.5, 2.0],
                colors=[style_cfg["electrode_fill"]], alpha=0.9, zorder=3)

    ax.contour(xx, yy, tumor, levels=[0.5], colors=["#333333"], linewidths=1.5, zorder=4)
    ax.contour(xx, yy, target, levels=[0.5], colors=[style_cfg["target_line"]],
               linewidths=1.2, linestyles="--", zorder=4)
    ax.contour(xx, yy, lesion, levels=[0.5], colors=[style_cfg["lesion_line"]], linewidths=2.0, zorder=5)

    (xmin, xmax), (ymin, ymax) = _case_limits()
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.set_xticks([-20, 0, 20]); ax.set_yticks([-20, 0, 20])

    if show_xlabel:
        ax.set_xlabel("x (mm)")
    else:
        ax.set_xlabel("")
        ax.set_xticklabels([])
    if show_ylabel:
        ax.set_ylabel("y (mm)")
    else:
        ax.set_ylabel("")
        ax.set_yticklabels([])

    ax.text(0.02, 1.03, f"{panel_label} {short_label}", transform=ax.transAxes, fontweight="bold")
    if add_scale_bar:
        _add_scale_bar(ax, 10.0, -21.0, -20.5, style_cfg)


def _metric_matrix(df: pd.DataFrame, protocol: str, metric: str, gaps: List[float], diameters: List[float]) -> np.ndarray:
    arr = np.zeros((len(diameters), len(gaps)), dtype=float)
    sub = df[(df["protocol_label"] == protocol) & (df["has_vessel"] == 1)]
    for i, d in enumerate(diameters):
        for j, g in enumerate(gaps):
            row = sub[(np.isclose(sub["vessel_diameter_mm"], d)) & (np.isclose(sub["gap_mm"], g))].iloc[0]
            arr[i, j] = float(row[metric])
    return arr


def make_fig1(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)

    fig, axes = plt.subplots(1, 3, figsize=(11.2, 4.0), gridspec_kw={"width_ratios": [1.05, 1.05, 1.12]})
    for ax in axes:
        _concept_panel(ax, style_cfg)

    # (A) Geometry
    ax = axes[0]
    ax.set_aspect("equal")
    ax.set_xlim(-20, 28)
    ax.set_ylim(-18, 18)
    target = patches.Circle((0, 0), radius=12.5, fill=False, edgecolor=style_cfg["target_line"], linestyle="--", linewidth=1.8)
    tumor = patches.Circle((0, 0), radius=7.5, facecolor=style_cfg["tumor_fill"], alpha=0.42, edgecolor="#333333", linewidth=1.4)
    vessel = patches.Circle((14.5, 0), radius=2.5, facecolor=style_cfg["vessel_fill"], edgecolor="#3F6D7A", linewidth=1.3)
    electrode = patches.Rectangle((-0.55, -10), 1.1, 20, facecolor=style_cfg["electrode_fill"], alpha=0.92, edgecolor="none")
    for obj in (target, tumor, vessel, electrode):
        ax.add_patch(obj)
    ax.annotate("", xy=(7.4, -6.6), xytext=(11.8, -6.6),
                arrowprops=dict(arrowstyle="<->", color=style_cfg["accent_color"], lw=1.3))
    ax.text(9.6, -8.6, "gap", ha="center", va="top", color=style_cfg["accent_color"])
    ax.annotate("", xy=(17.3, -2.5), xytext=(17.3, 2.5),
                arrowprops=dict(arrowstyle="<->", color="#3F6D7A", lw=1.25))
    ax.text(18.7, 0, "diameter", rotation=90, va="center", color="#3F6D7A")
    ax.text(0.02, 1.03, "(A) Parameterized geometry", transform=ax.transAxes, fontweight="bold")
    ax.text(-9.2, 8.8, "tumor")
    ax.text(-15.3, 13.0, "target margin")
    ax.text(-2.5, -12.3, "electrode")
    ax.text(11.2, 5.5, "vessel")
    ax.axis("off")

    # (B) Endpoints
    ax = axes[1]
    ax.set_aspect("equal")
    ax.set_xlim(-20, 24)
    ax.set_ylim(-18, 18)
    target = patches.Circle((0, 0), radius=12.5, fill=False, edgecolor=style_cfg["target_line"], linestyle="--", linewidth=1.8)
    tumor = patches.Circle((0, 0), radius=7.5, facecolor=style_cfg["tumor_fill"], alpha=0.42, edgecolor="#333333", linewidth=1.4)
    vessel = patches.Circle((14.5, 0), radius=2.5, facecolor=style_cfg["vessel_fill"], edgecolor="#3F6D7A", linewidth=1.2)
    for obj in (target, tumor, vessel):
        ax.add_patch(obj)

    theta = np.linspace(-np.pi, np.pi, 400)
    phi = np.arctan2(np.sin(theta), np.cos(theta))
    r = 15.0 - 5.2 * np.exp(-(phi / 0.32) ** 2) + 0.6 * np.cos(2 * theta)
    x = r * np.cos(theta)
    y = 0.96 * r * np.sin(theta)
    ax.plot(x, y, color=style_cfg["lesion_line"], lw=2.5)

    wedge = patches.Wedge((0, 0), 8.8, -21, 21, width=1.3,
                          facecolor="#FFE0B5", edgecolor="#FF9F3D", alpha=0.95)
    ax.add_patch(wedge)
    ax.text(0.02, 1.03, "(B) Shape-based endpoints", transform=ax.transAxes, fontweight="bold")
    ax.annotate("predicted lesion", xy=(-9.0, -13.0), xytext=(-16.5, -13.0),
                arrowprops=dict(arrowstyle="-", lw=0), color=style_cfg["lesion_line"], fontsize=8)
    ax.annotate("desired 5-mm margin", xy=(-11.5, 11.8), xytext=(-16.5, 12.0),
                arrowprops=dict(arrowstyle="-", lw=0), color=style_cfg["target_line"], fontsize=8)
    ax.annotate("MDI", xy=(6.9, 0), xytext=(-15.0, -3.3),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="#FF9F3D"),
                color="#8A4F00", fontsize=8.2)
    ax.annotate("vessel-side\nundercoverage", xy=(8.7, 0), xytext=(11.7, 8.2),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="#FF9F3D"),
                color="#C46C00", fontsize=8.2)
    ax.axis("off")

    # (C) Workflow
    ax = axes[2]
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.02, 1.03, "(C) Planning workflow", transform=ax.transAxes, fontweight="bold")

    def add_box(x, y, w, h, fc, ec, title, body_lines):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.045",
                                     facecolor=fc, edgecolor=ec, linewidth=1.3)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h * 0.77, title, ha="center", va="center", fontweight="bold")
        ax.text(x + w / 2, y + h * 0.42, "\n".join(body_lines), ha="center", va="center")

    add_box(0.05, 0.60, 0.24, 0.28, "#EDF6F9", "#B5CDD5", "Inputs",
            ["gap", "vessel diameter", "protocol"])
    add_box(0.38, 0.52, 0.26, 0.36, "#FFF7E8", "#E5C891", "Solver",
            ["2D", "electro–thermal", "damage model"])
    add_box(0.72, 0.60, 0.22, 0.28, "#F4F0FF", "#CEC2FF", "Outputs",
            ["TCR", "MDI", "PPV_target", "VUA"])

    ax.annotate("", xy=(0.38, 0.74), xytext=(0.29, 0.74),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=style_cfg["accent_color"]))
    ax.annotate("", xy=(0.72, 0.74), xytext=(0.64, 0.74),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=style_cfg["accent_color"]))

    chip1 = patches.FancyBboxPatch((0.09, 0.20), 0.34, 0.10, boxstyle="round,pad=0.02,rounding_size=0.04",
                                   facecolor="#F8F4ED", edgecolor="#D8C7AA", linewidth=1.0)
    chip2 = patches.FancyBboxPatch((0.53, 0.20), 0.31, 0.10, boxstyle="round,pad=0.02,rounding_size=0.04",
                                   facecolor="#F7F2FF", edgecolor="#D5C7FF", linewidth=1.0)
    ax.add_patch(chip1); ax.add_patch(chip2)
    ax.text(0.26, 0.25, "Primary: TCR, MDI", ha="center", va="center", fontsize=8.0)
    ax.text(0.685, 0.25, "Supplementary: PPV_target, VUA", ha="center", va="center", fontsize=8.0)

    fig.subplots_adjust(wspace=0.18)
    _save(fig, "Fig1_geometry_metric_definition", paths["output_main_dir"],
          cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def make_fig2(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    base_cfg = load_yaml(paths["base_config"])
    sweep_cfg = load_yaml(paths["protocol_sweep"])
    prot_lookup = _make_protocol_lookup(sweep_cfg)
    bind = Stage4Bindings(paths["source_stage_root"])

    fig, axes = plt.subplots(2, 2, figsize=(7.6, 7.2))
    cases = cfg["representative_cases"]
    for idx, (ax, case_cfg) in enumerate(zip(axes.ravel(), cases)):
        _, geom, fields, target = _rerun_case(bind, base_cfg, prot_lookup, case_cfg)
        row, col = divmod(idx, 2)
        _draw_contour_case(
            ax, geom, fields, target,
            case_cfg["panel_label"], case_cfg["short_label"], style_cfg,
            show_xlabel=(row == 1), show_ylabel=(col == 0),
            add_scale_bar=(idx == 3)
        )

    handles = [
        patches.Patch(facecolor=style_cfg["tumor_fill"], alpha=0.35, label="Tumor"),
        plt.Line2D([0], [0], color=style_cfg["target_line"], linestyle="--", lw=1.2, label="Target margin"),
        patches.Patch(facecolor=style_cfg["vessel_fill"], alpha=0.95, label="Vessel"),
        patches.Patch(facecolor=style_cfg["electrode_fill"], alpha=0.9, label="Electrode"),
        plt.Line2D([0], [0], color=style_cfg["lesion_line"], lw=2.0, label="Predicted lesion"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False,
               bbox_to_anchor=(0.5, -0.01), handlelength=2.2, columnspacing=1.6)
    fig.subplots_adjust(hspace=0.12, wspace=0.08, bottom=0.12)
    _save(fig, "Fig2_representative_contours", paths["output_main_dir"],
          cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def make_fig3(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    summary = pd.read_csv(paths["summary_csv"])
    sweep_cfg = load_yaml(paths["protocol_sweep"])
    protocols = [p["label"] for p in sweep_cfg["protocols"]]
    balanced = protocols[0]
    aggressive = protocols[1]
    gaps = [float(v) for v in sweep_cfg["grid"]["gaps_mm"]]
    diameters = [float(v) for v in sweep_cfg["grid"]["vessel_diameters_mm"]]

    m_bal = _metric_matrix(summary, balanced, "MDI", gaps, diameters)
    m_agg = _metric_matrix(summary, aggressive, "MDI", gaps, diameters)
    delta = m_bal - m_agg

    vmin = float(min(m_bal.min(), m_agg.min()))
    vmax = float(max(m_bal.max(), m_agg.max()))
    dmin = 0.0
    dmax = float(delta.max())

    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.7), gridspec_kw={"width_ratios": [1, 1, 1.05]})
    for ax in axes:
        _data_axis(ax, style_cfg)

    im1 = _heat(axes[0], m_bal, gaps, diameters, cmap="viridis", vmin=vmin, vmax=vmax, ylabel=True)
    axes[0].text(0.02, 1.03, "(A) Moderate-energy", transform=axes[0].transAxes, fontweight="bold")

    im2 = _heat(axes[1], m_agg, gaps, diameters, cmap="viridis", vmin=vmin, vmax=vmax, ylabel=False)
    axes[1].text(0.02, 1.03, "(B) High-energy", transform=axes[1].transAxes, fontweight="bold")

    im3 = _heat(axes[2], delta, gaps, diameters, cmap="OrRd", vmin=dmin, vmax=dmax, ylabel=False)
    axes[2].text(0.02, 1.03, "(C) MDI reduction", transform=axes[2].transAxes, fontweight="bold")

    cbar1 = fig.colorbar(im1, ax=axes[:2], fraction=0.035, pad=0.03)
    cbar1.set_label("MDI")
    cbar2 = fig.colorbar(im3, ax=axes[2], fraction=0.046, pad=0.04)
    cbar2.set_label("MDI reduction")
    fig.subplots_adjust(wspace=0.18)
    _save(fig, "Fig3_protocol_MDI_maps", paths["output_main_dir"],
          cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def make_fig4(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    summary = pd.read_csv(paths["summary_csv"])
    d_ref = float(cfg["tradeoff"]["vessel_diameter_mm"])

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.4))
    for ax in axes:
        _data_axis(ax, style_cfg)

    lines = []
    labels = []
    for label, color in [("balanced", style_cfg["balanced_color"]), ("aggressive", style_cfg["aggressive_color"])]:
        sub = summary[(summary["protocol_label"] == label) & (summary["has_vessel"] == 1) & (np.isclose(summary["vessel_diameter_mm"], d_ref))]
        sub = sub.sort_values("gap_mm")
        l1, = axes[0].plot(sub["gap_mm"], sub["MDI"], marker="o", color=color, linewidth=2.2, markersize=6, label=display_names[label])
        axes[1].plot(sub["gap_mm"], sub["PPV_target"], marker="o", color=color, linewidth=2.2, markersize=6)
        lines.append(l1); labels.append(display_names[label])

    axes[0].set_xlabel("Vessel gap (mm)"); axes[0].set_ylabel("MDI")
    axes[1].set_xlabel("Vessel gap (mm)"); axes[1].set_ylabel("PPV_target")
    axes[0].set_xticks([0, 2, 5]); axes[1].set_xticks([0, 2, 5])
    axes[0].text(0.02, 1.03, "(A) Margin deficit", transform=axes[0].transAxes, fontweight="bold")
    axes[1].text(0.02, 1.03, "(B) Target specificity", transform=axes[1].transAxes, fontweight="bold")
    fig.legend(lines, labels, frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.02))
    fig.subplots_adjust(wspace=0.26, top=0.82)
    _save(fig, "Fig4_tradeoff_MDI_PPV", paths["output_main_dir"],
          cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def make_figS1(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    conv = pd.read_csv(paths["convergence_csv"])
    severe = conv[conv["case_label"] == "severe_vessel"].copy()
    grid = severe[severe["group"] == "grid"].sort_values("grid_n")
    dt = severe[severe["group"] == "dt"].sort_values("dt_s", ascending=False)

    fig, axes = plt.subplots(2, 2, figsize=(8.2, 6.0))
    for ax in axes.ravel():
        _data_axis(ax, style_cfg)

    axes[0, 0].plot(grid["grid_n"], grid["TCR"], marker="o", color=style_cfg["balanced_color"], linewidth=2.0, markersize=5.5)
    axes[0, 0].set_xlabel("Grid size (n × n)"); axes[0, 0].set_ylabel("TCR")
    axes[0, 0].text(0.02, 1.03, "(A) Grid convergence: TCR", transform=axes[0, 0].transAxes, fontweight="bold")

    axes[0, 1].plot(grid["grid_n"], grid["MDI"], marker="o", color=style_cfg["aggressive_color"], linewidth=2.0, markersize=5.5)
    axes[0, 1].set_xlabel("Grid size (n × n)"); axes[0, 1].set_ylabel("MDI")
    axes[0, 1].text(0.02, 1.03, "(B) Grid convergence: MDI", transform=axes[0, 1].transAxes, fontweight="bold")

    axes[1, 0].plot(dt["dt_s"], dt["TCR"], marker="o", color=style_cfg["balanced_color"], linewidth=2.0, markersize=5.5)
    axes[1, 0].set_xlabel("Time step (s)"); axes[1, 0].set_ylabel("TCR")
    axes[1, 0].invert_xaxis()
    axes[1, 0].text(0.02, 1.03, "(C) Time-step check: TCR", transform=axes[1, 0].transAxes, fontweight="bold")

    axes[1, 1].plot(dt["dt_s"], dt["MDI"], marker="o", color=style_cfg["aggressive_color"], linewidth=2.0, markersize=5.5)
    axes[1, 1].set_xlabel("Time step (s)"); axes[1, 1].set_ylabel("MDI")
    axes[1, 1].invert_xaxis()
    axes[1, 1].text(0.02, 1.03, "(D) Time-step check: MDI", transform=axes[1, 1].transAxes, fontweight="bold")

    fig.subplots_adjust(hspace=0.30, wspace=0.26)
    _save(fig, "FigS1_convergence", paths["output_supp_dir"],
          cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def make_figS2_S3(cfg: dict, paths: dict) -> None:
    style_cfg = cfg["style"]
    apply_style(style_cfg)
    summary = pd.read_csv(paths["summary_csv"])
    sweep_cfg = load_yaml(paths["protocol_sweep"])
    gaps = [float(v) for v in sweep_cfg["grid"]["gaps_mm"]]
    diameters = [float(v) for v in sweep_cfg["grid"]["vessel_diameters_mm"]]

    spec = [
        ("TCR", "FigS2_TCR_maps", "TCR", "viridis", float(summary.loc[summary["has_vessel"] == 1, "TCR"].min()), 1.0, ".3f"),
        ("VUA_deg", "FigS3_VUA_maps", "VUA (deg)", "magma", float(summary.loc[summary["has_vessel"] == 1, "VUA_deg"].min()), float(summary.loc[summary["has_vessel"] == 1, "VUA_deg"].max()), "int"),
    ]

    for metric, stem, cbar_label, cmap, vmin, vmax, fmt in spec:
        mats = [_metric_matrix(summary, prot, metric, gaps, diameters) for prot in ["balanced", "aggressive"]]
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5))
        for k, (ax, mat, label) in enumerate(zip(axes, mats, ["(A) Moderate-energy", "(B) High-energy"])):
            _data_axis(ax, style_cfg)
            im = ax.imshow(mat, origin="lower", aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
            ax.set_xticks(np.arange(len(gaps))); ax.set_xticklabels([f"{g:g}" for g in gaps])
            ax.set_yticks(np.arange(len(diameters))); ax.set_yticklabels([f"{d:g}" for d in diameters])
            ax.set_xlabel("Vessel gap (mm)")
            if k == 0:
                ax.set_ylabel("Vessel diameter (mm)")
            else:
                ax.set_ylabel("")
                ax.set_yticklabels([])
            _annotate_heatmap(ax, mat, cmap, vmin, vmax, fmt=fmt)
            ax.text(0.02, 1.03, label, transform=ax.transAxes, fontweight="bold")
        cbar = fig.colorbar(im, ax=axes, fraction=0.04, pad=0.03)
        cbar.set_label(cbar_label)
        fig.subplots_adjust(wspace=0.12)
        _save(fig, stem, paths["output_supp_dir"],
              cfg["figures"]["export_pdf"], cfg["figures"]["export_png"], int(cfg["figures"]["png_dpi"]))


def make_all(config_path: str | Path, root: Path) -> None:
    cfg = load_yaml(root / config_path)
    paths = _resolve_paths(root, cfg)
    make_fig1(cfg, paths)
    make_fig2(cfg, paths)
    make_fig3(cfg, paths)
    make_fig4(cfg, paths)
    make_figS1(cfg, paths)
    make_figS2_S3(cfg, paths)
