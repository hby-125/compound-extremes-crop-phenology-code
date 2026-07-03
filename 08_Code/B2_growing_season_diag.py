# -*- coding: utf-8 -*-
"""B2: Growing-season diagnostic.

A strict growing-season-windowed compound index requires daily ERA5-Land
reanalysis (full daily temperature + precipitation, not available on disk).
Instead, we run a defensible **diagnostic**:

  (i) Compute pixel-year correlations between the annual dry-hot compound
      index and seasonally concentrated heat indices (SU = days with Tmax>25°C,
      WSDI = warm-spell duration index) plus a precipitation control (RX5day,
      max 5-day precipitation). If the annual dry-hot index is just a
      relabelling of summer heat, it should correlate ≥0.7-0.8 with SU.

 (ii) Substitute SU + WSDI for dry-hot/wet-hot in the maize GSL two-way FE
      regression and check whether the headline effects can be reproduced by
      these summer-concentrated proxies. If they cannot, the compound dimension
      contributes information beyond seasonal heat.

Outputs: out/p1_growing_season_diag.csv (correlations + regression coefs)
"""
import os, json, numpy as np, pandas as pd, sys
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
CACHE = str(DATA / "05_Climate_Data" / "china_cube_2000_2019.npz")
OUT = str(OUTPUTS / "tables")
os.makedirs(OUT, exist_ok=True)

COMP = ["dry_hot","wet_hot","dry_cold","wet_cold"]
MARG = ["TXx","TNn","PRCPTOT","CDD"]
COMPz = [c+"_z" for c in COMP]; MARGz = [c+"_z" for c in MARG]

# Load maize panel + cube
mz = pd.read_parquet(os.path.join(PAN, "panel_maize.parquet"))
z = np.load(CACHE)

# We already have SU/WSDI/RX5day in the cube but not in the pixel panel.
# Re-attach them by re-running the climate-attach step on existing lat/lon.
# Simpler: use the values already stored on the pixel-year level via cell index
# (the existing panel has dry_hot/wet_hot/... attached but maybe SU/WSDI too).
print("Panel columns:", [c for c in mz.columns if c.upper() == c or c in ("SU","WSDI","RX5day")])
# Confirm whether SU, WSDI, RX5day are in the panel; they should be (built earlier).
need = ["SU","WSDI","RX5day"]
have = [c for c in need if c in mz.columns]
miss = [c for c in need if c not in mz.columns]
print(f"  Have: {have}; Missing: {miss}")
if miss:
    # Attach the missing indices from cube using stored lat/lon/year of each panel row
    lat_v = z["lat"]; lon_v = z["lon"]; years = z["years"]
    li = np.rint((lat_v[0]-mz["lat"].values)/0.1).astype(int)
    ci = np.rint((mz["lon"].values-lon_v[0])/0.1).astype(int)
    yi = (mz["year"].values - years[0]).astype(int)
    for v in miss:
        mz[v] = z[v][yi, li, ci]
        print(f"  attached {v}: mean={mz[v].mean():.2f}")

# Correlation diagnostic at pixel-year level
corr_vars = ["dry_hot","wet_hot","TXx","SU","WSDI","RX5day"]
corr_mat = mz[corr_vars].corr().round(3)
print("\nPixel-year correlations:")
print(corr_mat)
corr_mat.to_csv(os.path.join(OUT, "p1_gs_correlations.csv"))

# z-score regressors
d = mz.copy()
for v in COMP + MARG + ["SU","WSDI","RX5day"]:
    s = d[v].std()
    d[v+"_z"] = (d[v]-d[v].mean())/s if s>0 else 0.0

# Headline: original (already known)
print("\n=== Headline original (dry_hot, wet_hot in COMP) ===")
m_orig = feols(d, "gsl", COMPz+MARGz, absorb="pix", dummies=("year",), cluster="cell")
for v in COMP:
    c = float(m_orig.params[v+"_z"]); s = float(m_orig.bse[v+"_z"])
    p = float(m_orig.pvalues[v+"_z"])
    star = "***" if p<0.01 else ("**" if p<0.05 else ("*" if p<0.10 else ""))
    print(f"  {v:9s}: {c:+.3f}{star} ({s:.3f})  p={p:.4f}")

# Substitute: replace dry_hot and wet_hot with SU and WSDI in the headline spec
print("\n=== Substitution: SU + WSDI in place of dry_hot + wet_hot ===")
SUBST = ["SU","WSDI","dry_cold","wet_cold"]
m_sub = feols(d, "gsl", [v+"_z" for v in SUBST]+MARGz, absorb="pix", dummies=("year",), cluster="cell")
sub_recs = []
for v in SUBST:
    c = float(m_sub.params[v+"_z"]); s = float(m_sub.bse[v+"_z"])
    p = float(m_sub.pvalues[v+"_z"])
    star = "***" if p<0.01 else ("**" if p<0.05 else ("*" if p<0.10 else ""))
    print(f"  {v:9s}: {c:+.3f}{star} ({s:.3f})  p={p:.4f}")
    sub_recs.append(dict(spec="SU+WSDI substitution", var=v, coef=c, se=s, p=p))

# Horse-race: keep dry_hot/wet_hot AND add SU+WSDI
print("\n=== Horse-race: all four compound + SU + WSDI ===")
HR = COMP + ["SU","WSDI"]
m_hr = feols(d, "gsl", [v+"_z" for v in HR]+MARGz, absorb="pix", dummies=("year",), cluster="cell")
hr_recs = []
for v in HR:
    c = float(m_hr.params[v+"_z"]); s = float(m_hr.bse[v+"_z"])
    p = float(m_hr.pvalues[v+"_z"])
    star = "***" if p<0.01 else ("**" if p<0.05 else ("*" if p<0.10 else ""))
    print(f"  {v:9s}: {c:+.3f}{star} ({s:.3f})  p={p:.4f}")
    hr_recs.append(dict(spec="horse-race", var=v, coef=c, se=s, p=p))

# Save
all_recs = []
for v in COMP+MARG:
    c = float(m_orig.params[v+"_z"]); s = float(m_orig.bse[v+"_z"]); p = float(m_orig.pvalues[v+"_z"])
    all_recs.append(dict(spec="baseline", var=v, coef=c, se=s, p=p))
all_recs.extend(sub_recs); all_recs.extend(hr_recs)
pd.DataFrame(all_recs).to_csv(os.path.join(OUT, "p1_growing_season_diag.csv"), index=False)
print("\nSaved:", os.path.join(OUT, "p1_growing_season_diag.csv"))
print("Saved:", os.path.join(OUT, "p1_gs_correlations.csv"))
