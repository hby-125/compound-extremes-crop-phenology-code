# -*- coding: utf-8 -*-
"""Match crop-phenology 1km grid pixels to the China climate subcube and run
two-way (pixel + year) fixed-effects regressions of phenology on extreme-climate
indices, with SEs clustered at the 0.1-degree climate cell.

Outcome focus: growing-season length and key stage DOYs.
This is a feasibility / signal-detection pass, not the final paper spec.
"""
import os, sys, numpy as np, pandas as pd
from pyproj import Transformer
import statsmodels.api as sm
from pathlib import Path

# ---- Path configuration ----
ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", ROOT / "outputs"))
CACHE = str(DATA / "05_Climate_Data" / "china_cube_2000_2019.npz")
PHENO_DIR = str(DATA / "04_Grid_Panels")
OUTDIR = str(OUTPUTS)

# ESRI:102025 Asia North Albers Equal Area Conic (explicit proj4, offline-safe)
ALBERS = ("+proj=aea +lat_1=15 +lat_2=65 +lat_0=30 +lon_0=95 "
          "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")

CLIM_VARS = ["dry_hot","wet_hot","dry_cold","wet_cold","warmday_night","coldday_night",
             "TXx","WSDI","SU","TR","TNn","FD","PRCPTOT","CDD","RX5day","SDII","DTR"]

STAGE = {
    "maize": dict(file="grid_panel_maize.csv", start="v3_doy", head="he_doy", mat="ma_doy"),
    "wheat": dict(file="grid_panel_wheat.csv", start="gr_em_doy", head="he_doy", mat="ma_doy"),
    "rice":  dict(file="grid_panel_rice.csv",  start="tr_doy", head="he_doy", mat="ma_doy"),
}

def load_cube():
    z = np.load(CACHE)
    lat = z["lat"]; lon = z["lon"]; years = z["years"]
    cube = {v: z[v] for v in CLIM_VARS}
    return lat, lon, years, cube

def reproject(x, y):
    tr = Transformer.from_crs(ALBERS, "EPSG:4326", always_xy=True)
    lon, lat = tr.transform(x, y)
    return np.asarray(lon), np.asarray(lat)

def build_panel(crop, n_pixels=30000, seed=42, modulo=11, keep_rem=0):
    """Chunked CSV read with a deterministic per-pixel hash sample so that all
    years of a kept pixel are retained (~1/modulo of pixels)."""
    s = STAGE[crop]
    cols = ["year","grid_row","grid_col","x_center_m","y_center_m", s["start"], s["head"], s["mat"]]
    if crop == "rice":
        cols.append("rice_type")
    path = os.path.join(PHENO_DIR, s["file"])
    parts = []
    for chunk in pd.read_csv(path, usecols=cols, encoding="utf-8-sig", chunksize=500_000):
        if crop == "rice":
            chunk = chunk[chunk["rice_type"] == "早稻和一季稻"]
        h = (chunk["grid_row"].astype(np.int64) * 31 + chunk["grid_col"].astype(np.int64)) % modulo
        chunk = chunk[h == keep_rem]
        parts.append(chunk)
    df = pd.concat(parts, ignore_index=True)
    df = df.dropna(subset=[s["start"], s["mat"]])
    df["pix"] = df["grid_row"].astype(np.int64) * 100000 + df["grid_col"].astype(np.int64)

    # reproject unique pixels
    upix = df.drop_duplicates("pix")[["pix","x_center_m","y_center_m"]].copy()
    lon, lat = reproject(upix["x_center_m"].values, upix["y_center_m"].values)
    upix["lon"] = lon; upix["lat"] = lat
    df = df.merge(upix[["pix","lon","lat"]], on="pix", how="left")
    return df, s

def attach_climate(df, lat_v, lon_v, years, cube):
    lat0 = lat_v[0]; lon0 = lon_v[0]            # lat descending, lon ascending, step 0.1
    li = np.rint((lat0 - df["lat"].values) / 0.1).astype(int)
    ci = np.rint((df["lon"].values - lon0) / 0.1).astype(int)
    yi = (df["year"].values - years[0]).astype(int)
    valid = (li >= 0) & (li < len(lat_v)) & (ci >= 0) & (ci < len(lon_v)) & (yi >= 0) & (yi < len(years))
    df = df[valid].copy(); li = li[valid]; ci = ci[valid]; yi = yi[valid]
    df["cell"] = li * 100000 + ci
    for v in CLIM_VARS:
        df[v] = cube[v][yi, li, ci]
    return df

MARGINAL = ["TXx","TNn","PRCPTOT","CDD"]
COMPOUND = ["dry_hot","wet_hot","dry_cold","wet_cold"]

def zscore(df, cols):
    for c in cols:
        sd = df[c].std()
        df[c+"_z"] = (df[c] - df[c].mean())/sd if sd>0 else 0.0
    return df

def fit_block(d, yvar, xvars, yd, cluster):
    """OLS on already pixel-demeaned data, with year dummies; cluster-robust."""
    X = pd.concat([d[xvars].reset_index(drop=True), yd.reset_index(drop=True)], axis=1)
    X = sm.add_constant(X, has_constant="add")
    m = sm.OLS(d[yvar].reset_index(drop=True), X).fit(
        cov_type="cluster", cov_kwds={"groups": d[cluster].values})
    return m

def run_crop(crop, lat_v, lon_v, years, cube, n_pixels=30000):
    df, s = build_panel(crop, n_pixels=n_pixels)
    df = attach_climate(df, lat_v, lon_v, years, cube)
    df["gsl"] = df[s["mat"]] - df[s["start"]]
    df["mat"] = df[s["mat"]]
    df = df[(df["gsl"] > 20) & (df["gsl"] < 320)].copy()
    print(f"\n##### {crop.upper()}  pixels={df['pix'].nunique()}  cells={df['cell'].nunique()}  obs={len(df)}")
    print("lon %.2f-%.2f lat %.2f-%.2f | GSL %.1f(sd %.1f)" %
          (df.lon.min(), df.lon.max(), df.lat.min(), df.lat.max(), df.gsl.mean(), df.gsl.std()))

    zcols = MARGINAL + COMPOUND
    # report SDs in original units (for interpreting standardized coefs)
    sds = {c: float(df[c].std()) for c in zcols}
    df = zscore(df, zcols)
    mx = [c+"_z" for c in MARGINAL]; cx = [c+"_z" for c in COMPOUND]; fx = mx + cx

    out = [f"CROP={crop} obs={len(df)} pixels={df['pix'].nunique()} cells={df['cell'].nunique()}",
           "SDs(orig units): " + ", ".join(f"{c}={sds[c]:.2f}" for c in zcols)]
    tidy = []
    for yvar in ["gsl","mat"]:
        d = df.dropna(subset=[yvar]+fx+["cell","pix","year"]).copy()
        for c in [yvar]+fx:
            d[c] = d[c] - d.groupby("pix")[c].transform("mean")   # pixel FE
        yd = pd.get_dummies(d["year"], prefix="yr", drop_first=True).astype(float)
        m_marg = fit_block(d, yvar, mx, yd, "cell")
        m_full = fit_block(d, yvar, fx, yd, "cell")
        wald = m_full.wald_test([f"{c} = 0" for c in cx], scalar=True)
        inc_r2 = m_full.rsquared - m_marg.rsquared
        out.append(f"\n--- DV={yvar}  two-way FE, cluster=cell ({d['cell'].nunique()} cells) ---")
        res = pd.DataFrame({"coef": m_full.params, "se": m_full.bse,
                            "t": m_full.tvalues, "p": m_full.pvalues}).loc[fx]
        out.append(res.round(3).to_string())
        out.append(f"R2 marginal-only = {m_marg.rsquared:.4f} | +compound = {m_full.rsquared:.4f} | "
                   f"incremental R2 = {inc_r2:.4f}")
        out.append(f"Joint Wald on compound block: F={wald.statistic:.1f}, p={wald.pvalue:.2e}")
        for c in fx:
            tidy.append(dict(crop=crop, dv=yvar, var=c.replace("_z",""),
                             block=("compound" if c in cx else "marginal"),
                             coef=m_full.params[c], se=m_full.bse[c], p=m_full.pvalues[c]))
        print("\n".join(out[-4:]))
    return "\n".join(out), pd.DataFrame(tidy)

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    lat_v, lon_v, years, cube = load_cube()
    crops = sys.argv[1:] or ["maize"]
    allout, alltidy = [], []
    for crop in crops:
        txt, tidy = run_crop(crop, lat_v, lon_v, years, cube)
        allout.append(txt); alltidy.append(tidy)
    with open(os.path.join(OUTDIR, "twfe_pheno_climate.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(allout))
    pd.concat(alltidy, ignore_index=True).to_csv(
        os.path.join(OUTDIR, "coef_tidy.csv"), index=False, encoding="utf-8-sig")
    print("\nWROTE", os.path.join(OUTDIR, "twfe_pheno_climate.txt"), "and coef_tidy.csv")

if __name__ == "__main__":
    main()
