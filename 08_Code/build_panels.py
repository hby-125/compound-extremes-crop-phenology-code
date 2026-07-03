# -*- coding: utf-8 -*-
"""Build and cache reusable analysis panels (crop phenology x climate) and
double-cropping turnover panels. Saves parquet to out/panels/."""
import os, numpy as np, pandas as pd
from pyproj import Transformer
from pathlib import Path

# ---- Path configuration ----
ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", ROOT / "outputs"))
CACHE = str(DATA / "05_Climate_Data" / "china_cube_2000_2019.npz")
PHENO = str(DATA / "04_Grid_Panels")
OUTP  = str(OUTPUTS / "panels")
os.makedirs(OUTP, exist_ok=True)

ALBERS = ("+proj=aea +lat_1=15 +lat_2=65 +lat_0=30 +lon_0=95 "
          "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")
CLIM = ["dry_hot","wet_hot","dry_cold","wet_cold","warmday_night","coldday_night",
        "TXx","WSDI","SU","TR","TNn","FD","PRCPTOT","CDD","RX5day","SDII","DTR"]
MODULO = 11

def load_cube():
    z = np.load(CACHE)
    return z["lat"], z["lon"], z["years"], {v: z[v] for v in CLIM}

def read_grid(crop):
    files = {"maize":("grid_panel_maize.csv",["v3_doy","he_doy","ma_doy"]),
             "wheat":("grid_panel_wheat.csv",["gr_em_doy","he_doy","ma_doy"]),
             "rice": ("grid_panel_rice.csv", ["tr_doy","he_doy","ma_doy"])}
    fn, stages = files[crop]
    base = ["year","grid_row","grid_col","x_center_m","y_center_m"]
    cols = base + stages + (["rice_type"] if crop=="rice" else [])
    parts=[]
    for ch in pd.read_csv(os.path.join(PHENO,fn), usecols=cols, encoding="utf-8-sig", chunksize=500_000):
        h=(ch["grid_row"].astype(np.int64)*31 + ch["grid_col"].astype(np.int64)) % MODULO
        parts.append(ch[h==0])
    df=pd.concat(parts, ignore_index=True)
    df["pix"]=df["grid_row"].astype(np.int64)*100000 + df["grid_col"].astype(np.int64)
    return df, stages

def add_lonlat(df):
    up=df.drop_duplicates("pix")[["pix","x_center_m","y_center_m"]].copy()
    tr=Transformer.from_crs(ALBERS,"EPSG:4326",always_xy=True)
    lon,lat=tr.transform(up["x_center_m"].values, up["y_center_m"].values)
    up["lon"]=lon; up["lat"]=lat
    return df.merge(up[["pix","lon","lat"]],on="pix",how="left")

def attach_climate(df, lat_v, lon_v, years, cube):
    li=np.rint((lat_v[0]-df["lat"].values)/0.1).astype(int)
    ci=np.rint((df["lon"].values-lon_v[0])/0.1).astype(int)
    yi=(df["year"].values-years[0]).astype(int)
    ok=(li>=0)&(li<len(lat_v))&(ci>=0)&(ci<len(lon_v))&(yi>=0)&(yi<len(years))
    df=df[ok].copy(); li=li[ok]; ci=ci[ok]; yi=yi[ok]
    df["cell"]=li*100000+ci
    df["li"]=li; df["ci"]=ci; df["yi"]=yi
    for v in CLIM:
        df[v]=cube[v][yi,li,ci]
    return df

def region_tag(df):
    # North China = lat>=33; South<33 (rough Qinling-Huaihe line); plus a finer zone
    df["north"]=(df["lat"]>=33).astype(int)
    return df

def main():
    lat_v,lon_v,years,cube=load_cube()
    grids={}
    for crop in ["maize","wheat","rice"]:
        df,stages=read_grid(crop)
        df=add_lonlat(df)
        df=attach_climate(df,lat_v,lon_v,years,cube)
        df=region_tag(df)
        start,head,mat=stages
        df["gsl"]=df[mat]-df[start]
        df=df.rename(columns={start:"start_doy",head:"head_doy",mat:"mat_doy"})
        df=df[(df["gsl"]>20)&(df["gsl"]<320)]
        if crop=="rice":
            df["single_early"]=(df["rice_type"]=="早稻和一季稻").astype(int)
        keep=["pix","cell","year","lon","lat","north","start_doy","head_doy","mat_doy","gsl"]+CLIM+(["rice_type","single_early"] if crop=="rice" else [])
        out=df[keep].copy()
        out.to_parquet(os.path.join(OUTP,f"panel_{crop}.parquet"))
        print(f"{crop}: pixels={out['pix'].nunique()} cells={out['cell'].nunique()} obs={len(out)} "
              f"GSL {out.gsl.mean():.1f}({out.gsl.std():.1f})")
        grids[crop]=df

    # ---- turnover: wheat -> maize (winter wheat - summer maize rotation) ----
    w=grids["wheat"][["pix","year","mat_doy","lon","lat","cell"]].rename(columns={"mat_doy":"wheat_ma"})
    m=grids["maize"][["pix","year","start_doy"]].rename(columns={"start_doy":"maize_v3"})
    wm=w.merge(m,on=["pix","year"],how="inner")
    wm["turnover_wm"]=wm["maize_v3"]-wm["wheat_ma"]
    wm=wm[(wm["turnover_wm"]>-30)&(wm["turnover_wm"]<150)]
    # attach climate via stored cell/year (recompute indices from cell)
    wm["li"]=(wm["cell"]//100000).astype(int); wm["ci"]=(wm["cell"]%100000).astype(int)
    wm["yi"]=(wm["year"]-years[0]).astype(int)
    for v in CLIM: wm[v]=cube[v][wm["yi"].values,wm["li"].values,wm["ci"].values]
    wm["north"]=(wm["lat"]>=33).astype(int)
    wm[["pix","cell","year","lon","lat","north","wheat_ma","maize_v3","turnover_wm"]+CLIM].to_parquet(
        os.path.join(OUTP,"panel_turnover_wm.parquet"))
    print(f"turnover wheat->maize: pixels={wm['pix'].nunique()} obs={len(wm)} mean={wm.turnover_wm.mean():.1f}")

    # ---- turnover: early/single rice -> late rice (double rice) ----
    r=grids["rice"]
    early=r[r["single_early"]==1][["pix","year","mat_doy","lon","lat","cell"]].rename(columns={"mat_doy":"early_ma"})
    late =r[r["single_early"]==0][["pix","year","start_doy"]].rename(columns={"start_doy":"late_tr"})
    rr=early.merge(late,on=["pix","year"],how="inner")
    rr["turnover_rice"]=rr["late_tr"]-rr["early_ma"]
    rr=rr[(rr["turnover_rice"]>-30)&(rr["turnover_rice"]<120)]
    rr["li"]=(rr["cell"]//100000).astype(int); rr["ci"]=(rr["cell"]%100000).astype(int)
    rr["yi"]=(rr["year"]-years[0]).astype(int)
    for v in CLIM: rr[v]=cube[v][rr["yi"].values,rr["li"].values,rr["ci"].values]
    rr["north"]=(rr["lat"]>=33).astype(int)
    rr[["pix","cell","year","lon","lat","north","early_ma","late_tr","turnover_rice"]+CLIM].to_parquet(
        os.path.join(OUTP,"panel_turnover_rice.parquet"))
    print(f"turnover double-rice: pixels={rr['pix'].nunique()} obs={len(rr)} mean={rr.turnover_rice.mean():.1f}")

if __name__=="__main__":
    main()
