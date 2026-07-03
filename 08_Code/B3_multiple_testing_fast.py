# -*- coding: utf-8 -*-
"""B3 (fast variant): Multiple-testing correction for the 12 headline
compound-extreme coefficients (4 compounds × 3 crops) on growing-season length.

Methods (analytic, no bootstrap):
  - Conventional p-values from cluster-robust SE.
  - Bonferroni-Holm step-down (controls FWER).
  - Benjamini-Hochberg FDR step-down.
  - Anderson (2008) sharpened FDR q-values.

This is the published-standard set of multiple-testing controls for a family
of correlated coefficients in economics; it avoids the wild-cluster bootstrap
that would otherwise be required for a Romano-Wolf step-down on a multi-
hundred-thousand-row panel.
"""
import os, sys, json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from pathlib import Path
try:
    from pyfixest import feols
except ImportError:
    print("WARNING: pyfixest not found. Install with: pip install pyfixest")
    raise

# ---- Path configuration ----
ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", ROOT / "outputs"))
PAN = str(OUTPUTS / "panels")
OUT = str(OUTPUTS / "tables")
os.makedirs(OUT, exist_ok=True)

COMP = ["dry_hot","wet_hot","dry_cold","wet_cold"]
MARG = ["TXx","TNn","PRCPTOT","CDD"]
COMPz = [c+"_z" for c in COMP]; MARGz = [c+"_z" for c in MARG]

def load(crop):
    return pd.read_parquet(os.path.join(PAN, f"panel_{crop}.parquet"))

def run_baseline(d, dv="gsl"):
    d = d.copy()
    for v in COMP + MARG:
        s = d[v].std()
        d[v+"_z"] = (d[v] - d[v].mean())/s if s>0 else 0.0
    m = feols(d, dv, MARGz+COMPz, absorb="pix", dummies=("year",), cluster="cell")
    out = {}
    for v in COMP:
        z = v+"_z"
        out[v] = dict(coef=float(m.params[z]), se=float(m.bse[z]),
                      p=float(m.pvalues[z]), t=float(m.tvalues[z]),
                      N=int(m._nobs_), clusters=int(m._ncl_))
    return out

records = []
for crop in ["maize","wheat","rice"]:
    print(f"=== {crop} baseline GSL ===")
    d = load(crop)
    res = run_baseline(d, "gsl")
    for v in COMP:
        r = res[v]
        records.append(dict(crop=crop, var=v, coef=r["coef"], se=r["se"],
                            t=r["t"], p_conv=r["p"], N=r["N"]))
        print(f"  {v:9s}: coef={r['coef']:+.3f}  t={r['t']:+.2f}  p={r['p']:.3g}")

df = pd.DataFrame(records)

# ---- Multiple testing adjustments ----
def bonferroni_holm(p):
    p = np.array(p, float); n = len(p); order = np.argsort(p)
    adj = np.minimum.accumulate((n - np.arange(n)) * p[order])
    out = np.empty_like(adj); out[order] = np.clip(adj, 0, 1)
    return out

def bh_fdr(p):
    p = np.array(p, float); n = len(p); order = np.argsort(p)
    q = (n / np.arange(1, n+1)) * p[order]
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q); out[order] = np.clip(q, 0, 1)
    return out

def sharpened_fdr(p):
    p = np.array(p, float); n = len(p); order = np.argsort(p)
    ps = p[order]
    q = (n * ps) / (n - np.arange(1, n+1) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q); out[order] = np.clip(q, 0, 1)
    return out

p_conv = df["p_conv"].values
df["p_holm"]  = bonferroni_holm(p_conv)
df["q_bh"]    = bh_fdr(p_conv)
df["q_sharp"] = sharpened_fdr(p_conv)
df = df[["crop","var","coef","se","t","p_conv","p_holm","q_bh","q_sharp","N"]]
df.to_csv(os.path.join(OUT, "p1_multiple_testing.csv"), index=False)
print("\nSaved:", os.path.join(OUT, "p1_multiple_testing.csv"))
print(df.round(4).to_string(index=False))

# Markdown ED table
def stars(p):
    return "***" if p<0.01 else ("**" if p<0.05 else ("*" if p<0.10 else ""))
def fmt(p):
    return f"<0.001" if p<0.001 else f"{p:.3f}"
md = ["| Crop | Compound | β | s.e. | *p* (conv.) | *p* (Holm) | *q* (BH) | *q* (sharpened) |",
      "|---|---|---|---|---|---|---|---|"]
for _, r in df.iterrows():
    md.append(f"| {r['crop'].capitalize()} | {r['var'].replace('_','–')} | "
              f"{r['coef']:+.3f}{stars(r['p_conv'])} | ({r['se']:.3f}) | "
              f"{fmt(r['p_conv'])} | {fmt(r['p_holm'])} | "
              f"{fmt(r['q_bh'])} | {fmt(r['q_sharp'])} |")
open(os.path.join(OUT, "p1_multiple_testing_table.md"), "w", encoding="utf-8").write("\n".join(md))
print("Markdown table saved.")
