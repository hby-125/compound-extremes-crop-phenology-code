# -*- coding: utf-8 -*-
"""A1: Extended Data Figure 1 — compound-event frequency trend and spatial
distribution of dry-hot compound, 2000-2019.

Generates a Nature-style vector PDF figure with:
  Panel (a): annual cropland-mean count of the four compound event days,
             with a 95% across-pixel CI band for the headline dry-hot trend.
  Panel (b): spatial distribution of mean dry-hot compound days over the
             maize-pixel sample of the analysis.

Style: Times font, B/W (panel (a) line styles vary), Nature-style panel labels."""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

# ---- Path configuration ----
ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", ROOT / "outputs"))
PAN = str(OUTPUTS / "panels")
OUT = str(OUTPUTS / "figures")
os.makedirs(OUT, exist_ok=True)

rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman","Times","DejaVu Serif"],
    "font.size": 9,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "pdf.fonttype": 42,   # embed TrueType (editable in Illustrator)
})

# ---------- Data ----------
mz = pd.read_parquet(os.path.join(PAN, "panel_maize.parquet"))

# Annual cropland-mean of each compound index
COMP = ["dry_hot","wet_hot","dry_cold","wet_cold"]
LABELS = {"dry_hot": "Dry–hot",
          "wet_hot": "Wet–hot",
          "dry_cold": "Dry–cold",
          "wet_cold": "Wet–cold"}
yr = mz.groupby("year")[COMP].mean()
# 95% across-pixel CI for the headline dry-hot
ci_dry = mz.groupby("year")["dry_hot"].quantile([0.025, 0.975]).unstack()

# ---------- Figure ----------
fig = plt.figure(figsize=(7.2, 3.4))
ax1 = fig.add_axes([0.085, 0.18, 0.40, 0.72])
ax2 = fig.add_axes([0.56, 0.10, 0.40, 0.80])

# Panel (a): annual mean lines, B/W with distinct linestyles
styles = {"dry_hot": ("-",  "k",  2.0),
          "wet_hot": ("--", "0.30", 1.3),
          "dry_cold":(":",  "0.45", 1.4),
          "wet_cold":("-.", "0.55", 1.2)}
# CI band for dry-hot (light grey)
ax1.fill_between(yr.index, ci_dry[0.025], ci_dry[0.975],
                 color="0.80", alpha=0.5, edgecolor="none",
                 label=None, zorder=1)
for v in COMP:
    ls, c, lw = styles[v]
    ax1.plot(yr.index, yr[v], linestyle=ls, color=c, linewidth=lw,
             marker="o" if v=="dry_hot" else None, markersize=3,
             label=LABELS[v])
ax1.set_xlabel("Year")
ax1.set_ylabel("Compound-event days (cropland mean)")
ax1.set_xlim(2000, 2019)
ax1.set_ylim(0, max(yr.max())*1.15)
ax1.set_xticks([2000, 2005, 2010, 2015, 2019])
ax1.legend(loc="upper left", frameon=False, fontsize=7.5, ncol=1, handlelength=2.2)
ax1.text(-0.18, 1.02, "a", transform=ax1.transAxes,
         fontsize=11, fontweight="bold", fontstyle="italic",
         va="bottom", ha="left")

# Panel (b): spatial distribution of mean dry-hot days over maize pixels
sp = mz.groupby(["lon","lat"])["dry_hot"].mean().reset_index()
# B/W-friendly: use a perceptually uniform single-hue (grayscale-like) colormap.
# For Nature-style B/W, use Greys with a clear gradient.
sc = ax2.scatter(sp["lon"], sp["lat"], c=sp["dry_hot"], s=1.0,
                 cmap="Greys", vmin=5, vmax=45,
                 marker="s", linewidths=0)
# Coastline-equivalent bounds: tight axes
ax2.set_xlim(73, 135); ax2.set_ylim(18, 54)
ax2.set_xlabel("Longitude (°E)")
ax2.set_ylabel("Latitude (°N)")
ax2.set_aspect(1.0)
# Colorbar
cax = fig.add_axes([0.965, 0.13, 0.013, 0.74])
cb = plt.colorbar(sc, cax=cax, orientation="vertical")
cb.outline.set_linewidth(0.5)
cb.set_label("Days yr$^{-1}$", fontsize=8)
cb.ax.tick_params(labelsize=7.5, width=0.5)
ax2.text(-0.18, 1.02, "b", transform=ax2.transAxes,
         fontsize=11, fontweight="bold", fontstyle="italic",
         va="bottom", ha="left")

# Save vector PDF
pdf = os.path.join(OUT, "Extended_Data_Figure_1.pdf")
png = os.path.join(OUT, "Extended_Data_Figure_1.png")
fig.savefig(pdf, format="pdf", bbox_inches="tight")
fig.savefig(png, dpi=300, bbox_inches="tight")
print("saved:", pdf, "and", png)

# Source data csv for Source_Data.xlsx
src = pd.DataFrame({"year": yr.index})
for v in COMP: src[LABELS[v]] = yr[v].values
src["dry_hot_p025"] = ci_dry[0.025].reindex(yr.index).values
src["dry_hot_p975"] = ci_dry[0.975].reindex(yr.index).values
src.to_csv(os.path.join(OUT, "ED_Figure_1_panel_a_data.csv"), index=False)
sp.to_csv(os.path.join(OUT, "ED_Figure_1_panel_b_data.csv"), index=False)
print("source data:", "ED_Figure_1_panel_a_data.csv", "ED_Figure_1_panel_b_data.csv")
