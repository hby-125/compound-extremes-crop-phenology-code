# -*- coding: utf-8 -*-
"""Generate publication-grade vector figures for the Food Policy paper:
Figure 1 (conceptual framework), Figure 2 (nutrition transition), Figure 3
(compound climate over Chinese cropland), Figure 4 (climate to diet),
and Figure A1 (randomization placebo).

Output: PDF (primary, vector) + SVG (backup, vector). Black-and-white only;
visual differentiation via line style, marker shape, fill hatching, and
grayscale. Times serif font; pdf.fonttype = 42 (embedded TrueType).
"""

import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D
from pathlib import Path

# ---- Path configuration ----
# NOTE: This script generates vector figures for the companion Food Policy / CHNS paper.
# It reads pre-computed regression tables and panels.
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", REPO_ROOT / "outputs"))
DATA = Path(os.environ.get("DATA_DIR", REPO_ROOT / "data"))
OUT = str(OUTPUTS / "figures")
os.makedirs(OUT, exist_ok=True)
TAB = str(OUTPUTS / "tables")
TAB2 = str(OUTPUTS / "tables_v2")
PAN = str(OUTPUTS / "panels")
CACHE = str(DATA / "05_Climate_Data" / "china_cube_2000_2019.npz")

def save(fig, name):
    pdf = os.path.join(OUT, name + ".pdf")
    svg = os.path.join(OUT, name + ".svg")
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.05)
    fig.savefig(svg, bbox_inches="tight", pad_inches=0.05)
    print(f"  -> {pdf}")
    print(f"  -> {svg}")

# ====================================================================
# Figure 1. Conceptual framework: a buffered climate→phenology→diet channel
# ====================================================================
def figure_1():
    print("Figure 1: conceptual framework")
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5.5); ax.axis("off")

    # Three primary boxes
    def box(x, y, w, h, title, sub):
        b = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle="round,pad=0.04,rounding_size=0.10",
                           linewidth=0.9, edgecolor="black", facecolor="white", zorder=3)
        ax.add_patch(b)
        ax.text(x, y + h/2 - 0.30, title, ha="center", va="center",
                fontsize=10, fontweight="bold", zorder=4)
        ax.text(x, y - h/2 + 0.32, sub, ha="center", va="center",
                fontsize=8, style="italic", zorder=4)

    # Layout y = 3.0 for the main row
    y0 = 3.0; w = 2.4; h = 1.4
    box(1.5, y0, w, h, "Compound climate", "Global 0.1° panel\n(1950–2025)")
    box(5.0, y0, w, h, "Crop phenology",  "ChinaCropPhen1km\n(2000–2019)")
    box(8.5, y0, w, h, "Household diet",  "CHNS\n(50,463 person-waves)")

    # H1 solid arrow (climate → phenology)
    a1 = FancyArrowPatch((2.7, y0), (3.8, y0), arrowstyle="-|>",
                        mutation_scale=14, linewidth=1.4, color="black", zorder=2)
    ax.add_patch(a1)
    ax.text(3.25, y0 + h/2 + 0.20, "H1", ha="center", fontsize=9.5,
            fontweight="bold")
    ax.text(3.25, y0 - h/2 - 0.22, "+2.7 days/SD", ha="center", fontsize=7.5,
            style="italic")

    # H4 dashed arrow (phenology → diet, weak)
    a2 = FancyArrowPatch((6.2, y0), (7.3, y0), arrowstyle="-|>",
                        mutation_scale=14, linewidth=1.0, color="black",
                        linestyle=(0, (4, 2)), zorder=2)
    ax.add_patch(a2)
    ax.text(6.75, y0 + h/2 + 0.20, "H4 (rejected)", ha="center", fontsize=9.5,
            fontweight="bold")
    ax.text(6.75, y0 - h/2 - 0.22, "mediation share = −9.3%", ha="center",
            fontsize=7.5, style="italic")

    # H2: market buffering callout (above diet box, pointing down)
    bx = FancyBboxPatch((6.6, 4.5), 3.8, 0.85,
                       boxstyle="round,pad=0.03,rounding_size=0.06",
                       linewidth=0.7, edgecolor="black",
                       facecolor=(0.93, 0.93, 0.93), zorder=3)
    ax.add_patch(bx)
    ax.text(8.5, 4.92, "H2:  Market buffering", ha="center", va="center",
            fontsize=8.5, fontweight="bold", zorder=4)
    ax.text(8.5, 4.65, "grain reserves · food trade · off-farm income",
            ha="center", va="center", fontsize=7.5, style="italic", zorder=4)
    aB = FancyArrowPatch((8.5, 4.5), (8.5, y0 + h/2 + 0.05),
                        arrowstyle="-|>", mutation_scale=12, linewidth=0.9,
                        color="black", zorder=2)
    ax.add_patch(aB)

    # H3: farm-household residual differential (below diet box, pointing up)
    bx2 = FancyBboxPatch((6.6, 0.25), 3.8, 0.95,
                       boxstyle="round,pad=0.03,rounding_size=0.06",
                       linewidth=0.7, edgecolor="black",
                       facecolor=(0.93, 0.93, 0.93), zorder=3,
                       linestyle="--")
    ax.add_patch(bx2)
    ax.text(8.5, 0.92, "H3:  Farm-household differential", ha="center",
            va="center", fontsize=8.5, fontweight="bold", zorder=4)
    ax.text(8.5, 0.55, "−0.20 food groups / SD dry-hot\n(p < 0.01; province × year FE)",
            ha="center", va="center", fontsize=7.5, style="italic", zorder=4)
    aB2 = FancyArrowPatch((8.5, 1.20), (8.5, y0 - h/2 - 0.05),
                        arrowstyle="-|>", mutation_scale=12, linewidth=0.9,
                        color="black", linestyle=(0, (4, 2)), zorder=2)
    ax.add_patch(aB2)

    # Legend at bottom
    leg_items = [
        Line2D([0], [0], color="black", lw=1.4, label="Strong / confirmed link"),
        Line2D([0], [0], color="black", lw=1.0, linestyle=(0, (4, 2)),
               label="Hypothesised-weak or broken link"),
    ]
    ax.legend(handles=leg_items, loc="lower left", bbox_to_anchor=(0.02, -0.02),
              fontsize=8, frameon=False)

    save(fig, "Figure_1_conceptual_framework")
    plt.close(fig)

# ====================================================================
# Figure 2. Nutrition transition in CHNS, 2000–2011
# ====================================================================
def figure_2():
    print("Figure 2: nutrition transition")
    f = json.load(open(os.path.join(TAB, "facts2.json")))
    d = pd.read_parquet(os.path.join(PAN, "chns_nutrition.parquet"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.0))

    waves = sorted([int(k) for k in f["fat_share_by_wave"].keys()])
    all_ = [f["fat_share_by_wave"][str(w)] for w in waves]
    rural = [f["fat_rural_by_wave"][str(w)] for w in waves]
    urban = [f["fat_urban_by_wave"][str(w)] for w in waves]

    # Panel (a): fat-energy share
    ax1.plot(waves, all_,   color="black", linestyle="-",  marker="o",
             markersize=5, linewidth=1.4, label="All",   markerfacecolor="black",
             markeredgecolor="black")
    ax1.plot(waves, rural,  color="black", linestyle="--", marker="s",
             markersize=5, linewidth=1.1, label="Rural", markerfacecolor="white",
             markeredgecolor="black")
    ax1.plot(waves, urban,  color="black", linestyle=":",  marker="^",
             markersize=5.5, linewidth=1.1, label="Urban", markerfacecolor=(0.6, 0.6, 0.6),
             markeredgecolor="black")
    ax1.set_xlabel("Survey year")
    ax1.set_ylabel("Fat-energy share")
    ax1.set_title("(a) Fat-energy share by area", loc="left", pad=4)
    ax1.set_ylim(0.24, 0.38)
    ax1.set_xticks(waves)
    ax1.legend(loc="lower right", handlelength=2.5)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # Panel (b): DDS by wave & rural status (waves with DDS = 2004–2011)
    dds = d.dropna(subset=["dds"]).groupby(["wave", "rural"])["dds"].mean().unstack()
    dds = dds.rename(columns={0: "Urban", 1: "Rural"})
    ax2.plot(dds.index, dds["Rural"], color="black", linestyle="--", marker="s",
             markersize=5, linewidth=1.1, label="Rural", markerfacecolor="white",
             markeredgecolor="black")
    ax2.plot(dds.index, dds["Urban"], color="black", linestyle=":", marker="^",
             markersize=5.5, linewidth=1.1, label="Urban",
             markerfacecolor=(0.6, 0.6, 0.6), markeredgecolor="black")
    ax2.set_xlabel("Survey year")
    ax2.set_ylabel("Dietary diversity score (groups)")
    ax2.set_title("(b) Dietary diversity by area", loc="left", pad=4)
    ax2.set_xticks(dds.index)
    ax2.legend(loc="lower right", handlelength=2.5)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)

    fig.tight_layout()
    save(fig, "Figure_2_nutrition_transition")
    plt.close(fig)

# ====================================================================
# Figure 3. Compound climate extremes over Chinese cropland, 2000–2019
# ====================================================================
def figure_3():
    print("Figure 3: compound climate")
    mz = pd.read_parquet(os.path.join(PAN, "panel_maize.parquet"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 3.2))

    # Panel (a): annual cropland-mean compound-event days, 4 indicators
    styles = [
        ("dry_hot",  "-",   "o",  1.6, "black",        "black"),
        ("wet_hot",  "--",  "s",  1.2, "black",        "white"),
        ("dry_cold", ":",   "^",  1.2, "black",        (0.6, 0.6, 0.6)),
        ("wet_cold", "-.",  "D",  1.0, (0.45,)*3,      "white"),
    ]
    for v, ls, mk, lw, ec, mfc in styles:
        s = mz.groupby("year")[v].mean()
        ax1.plot(s.index, s.values, linestyle=ls, marker=mk, color=ec,
                 markersize=4, linewidth=lw, label=v.replace("_", "–"),
                 markerfacecolor=mfc, markeredgecolor=ec)
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Compound-event days per year\n(cropland mean)")
    ax1.set_title("(a) Compound climate extremes, 2000–2019", loc="left", pad=4)
    ax1.legend(loc="upper left", ncol=2, columnspacing=1.0, handlelength=2.6)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # Panel (b): spatial scatter of mean dry_hot over maize pixels (grayscale)
    s = mz.groupby(["lon", "lat"])["dry_hot"].mean().reset_index()
    sc = ax2.scatter(s["lon"], s["lat"], c=s["dry_hot"], cmap="Greys",
                     s=1.5, vmin=5, vmax=45, marker="s", edgecolors="none",
                     rasterized=True)
    ax2.set_xlabel("Longitude (°E)")
    ax2.set_ylabel("Latitude (°N)")
    ax2.set_title("(b) Mean dry-hot days, maize pixels", loc="left", pad=4)
    ax2.set_aspect("equal")
    cb = fig.colorbar(sc, ax=ax2, fraction=0.045, pad=0.04)
    cb.set_label("days/yr", rotation=270, labelpad=10, fontsize=8)
    cb.ax.tick_params(labelsize=7, width=0.5)
    for s_ in ("top", "right"):
        ax2.spines[s_].set_visible(False)

    fig.tight_layout()
    save(fig, "Figure_3_compound_climate")
    plt.close(fig)

# ====================================================================
# Figure 4. From climate to diet
# ====================================================================
def figure_4():
    print("Figure 4: climate to diet")
    rd = pd.read_csv(os.path.join(TAB, "t2_reduced.csv"), encoding="utf-8-sig")
    ag = pd.read_csv(os.path.join(TAB, "t4_agchannel.csv"), encoding="utf-8-sig")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 3.4))

    MARG = ["TXx", "TNn", "PRCPTOT", "CDD"]
    COMP = ["dry_hot", "wet_hot", "dry_cold", "wet_cold"]
    order = MARG + COMP

    # Panel (a): reduced-form coefficients on DDS
    d = rd[rd["dv"] == "dds"].set_index("var").reindex(order)
    y_pos = np.arange(len(order))[::-1]  # top: marginals; bottom: compound
    for i, var in enumerate(order):
        c, s = d.loc[var, "coef"], d.loc[var, "se"]
        # Marker style: open square for marginal, filled circle for compound
        marker = "s" if var in MARG else "o"
        fc = "white" if var in MARG else "black"
        # 95% CI whisker
        ax1.errorbar(c, y_pos[i], xerr=1.96 * s, fmt=marker, color="black",
                     ecolor="black", elinewidth=0.8, capsize=2.5, capthick=0.6,
                     markersize=5.5, markerfacecolor=fc, markeredgecolor="black",
                     markeredgewidth=0.8)
    ax1.axvline(0, color="black", linewidth=0.6, linestyle="-")
    # Subtle dividing line between MARG block and COMP block
    ax1.axhline(y_pos[len(MARG)] + 0.5, color="black", linewidth=0.4,
                linestyle=":")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels([v.replace("_", "–") for v in order])
    ax1.set_xlabel("Effect on dietary diversity (groups per +1 SD)")
    ax1.set_title("(a) Reduced form on DDS", loc="left", pad=4)
    # Marker-shape legend (replaces inline Marginal/Compound text annotations)
    leg_a = [
        Line2D([0], [0], marker="s", linestyle="None", markerfacecolor="white",
               markeredgecolor="black", markersize=6, label="Marginal index"),
        Line2D([0], [0], marker="o", linestyle="None", markerfacecolor="black",
               markeredgecolor="black", markersize=6, label="Compound extreme"),
    ]
    ax1.legend(handles=leg_a, loc="lower left", handlelength=1.2, fontsize=7.5,
               borderpad=0.3)
    for s_ in ("top", "right"):
        ax1.spines[s_].set_visible(False)

    # Panel (b): farm-channel interactions on DDS (bar chart)
    a = ag[(ag["moderator"] == "farm_hh") & (ag["dv"] == "dds")] \
        .set_index("var").reindex(COMP)
    x = np.arange(len(COMP))
    coefs = a["coef"].values; ses = a["se"].values; ps = a["p"].values
    # Bars: filled black for p<0.05; hatched white for non-sig
    bars = []
    for i, (c, p) in enumerate(zip(coefs, ps)):
        if p < 0.05:
            b = ax2.bar(x[i], c, width=0.55, color="black",
                        edgecolor="black", linewidth=0.6)
        else:
            b = ax2.bar(x[i], c, width=0.55, color="white",
                        edgecolor="black", linewidth=0.6, hatch="////")
        bars.append(b)
    ax2.errorbar(x, coefs, yerr=1.96 * ses, fmt="none", ecolor="black",
                 elinewidth=0.8, capsize=2.5, capthick=0.6)
    ax2.axhline(0, color="black", linewidth=0.6)
    ax2.set_xticks(x)
    ax2.set_xticklabels([c.replace("_", "–") for c in COMP], rotation=15)
    ax2.set_ylabel("Differential effect on DDS\n(farm vs non-farm, per +1 SD)")
    ax2.set_title("(b) Agricultural channel\n(compound × farm-household)",
                  loc="left", pad=4, fontsize=9.5)
    # Legend for bar styles
    leg = [
        Rectangle((0, 0), 1, 1, facecolor="black", edgecolor="black",
                  label="p < 0.05"),
        Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="black",
                  hatch="////", label="p ≥ 0.05"),
    ]
    ax2.legend(handles=leg, loc="upper right", handlelength=1.5)
    for s_ in ("top", "right"):
        ax2.spines[s_].set_visible(False)

    fig.tight_layout()
    save(fig, "Figure_4_climate_to_diet")
    plt.close(fig)

# ====================================================================
# Figure A1. Randomization-inference placebo distribution
# ====================================================================
def figure_A1():
    print("Figure A1: placebo distribution")
    perm = pd.read_csv(os.path.join(TAB2, "perm_dryhot_dds.csv"))["theta_perm"].values
    summary = json.load(open(os.path.join(TAB2, "perm_summary.json")))
    true_theta = summary["true_theta"]
    placebo_p = summary["placebo_p_two_sided"]
    pct = summary["observed_percentile"]

    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.hist(perm, bins=42, color="white", edgecolor="black", linewidth=0.5,
            hatch="..", zorder=2)
    ax.axvline(true_theta, color="black", linewidth=1.6, zorder=3,
               label=f"Observed θ = {true_theta:+.3f}")
    ax.axvline(0, color="black", linewidth=0.5, linestyle="--",
               alpha=0.5, zorder=2)
    ax.set_xlabel(r"$\theta$ (dry-hot $\times$ Farm) on DDS, permuted farm status")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Figure A1.  Randomization-inference placebo distribution\n"
                 f"(n = {len(perm)} within-province × year permutations; "
                 f"placebo p = {placebo_p:.3f}; observed θ at {pct:.1f}th percentile)",
                 loc="left", fontsize=9, pad=6)
    ax.legend(loc="upper right", handlelength=1.6)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    fig.tight_layout()
    save(fig, "Figure_A1_placebo_distribution")
    plt.close(fig)

# ====================================================================
if __name__ == "__main__":
    print(f"Output directory: {OUT}\n")
    figure_1()
    figure_2()
    figure_3()
    figure_4()
    figure_A1()
    print("\nAll five vector figures generated (PDF + SVG, B&W, Times serif).")
