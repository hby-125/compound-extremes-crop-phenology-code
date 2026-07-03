# -*- coding: utf-8 -*-
"""Dietary diversity score (DDS) per (IDind, wave) from CHNS individual food
records nutr3_00, mapped to food groups (归并组). Augments chns_nutrition.parquet."""
import os, numpy as np, pandas as pd
from pathlib import Path

# ---- Path configuration ----
# NOTE: This script requires CHNS survey data (not included in the standard data archive).
# Set CHNS_DIR environment variable or edit the path below.
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", REPO_ROOT / "outputs"))
CH = os.environ.get("CHNS_DIR", str(REPO_ROOT / "data" / "chns"))
PAN = str(OUTPUTS / "panels" / "chns_nutrition.parquet")
WAVES=[2004,2006,2009,2011]

mp=pd.read_csv(CH+r"\CHNS食物编码-分组对照表_2004-2011.csv",encoding="utf-8-sig")
mp=mp.dropna(subset=["foodcode_6位","归并组"])
mp["foodcode_6位"]=mp["foodcode_6位"].astype("int64")
g2=dict(zip(mp["foodcode_6位"],mp["归并组"]))
cat=dict(zip(mp["foodcode_6位"],mp["成分表大类码"]))
ANIMAL=set(mp.loc[mp["大类名称"].astype(str).str.contains("肉|禽|鱼|虾|蛋|乳|奶|水产",na=False),"成分表大类码"].unique().tolist())
print("food groups:",sorted(mp["归并组"].dropna().unique().tolist()))
print("animal major-codes:",sorted([int(x) for x in ANIMAL if pd.notna(x)]))

fpath=CH+r"\Master_Nutrition_201410\Master_Nutrition_201410\nutr3_00.dta"
parts=[]
it=pd.read_stata(fpath, columns=["IDind","wave","foodcode"], convert_categoricals=False, chunksize=400_000)
for ch in it:
    ch=ch[ch["wave"].isin(WAVES)].dropna(subset=["IDind","wave","foodcode"])
    if len(ch)==0: continue
    ch=ch.copy()
    ch["IDind"]=ch["IDind"].astype("int64"); ch["wave"]=ch["wave"].astype("int64"); ch["foodcode"]=ch["foodcode"].astype("int64")
    ch["grp"]=ch["foodcode"].map(g2)
    ch["animal"]=ch["foodcode"].map(cat).isin(ANIMAL)
    parts.append(ch[["IDind","wave","foodcode","grp","animal"]])
f=pd.concat(parts,ignore_index=True)
print("food records (2004-2011):",len(f),"mapped grp share:",f["grp"].notna().mean().round(3))

agg=f.groupby(["IDind","wave"]).agg(
    dds=("grp",lambda s:s.dropna().nunique()),
    nfoods=("foodcode","nunique"),
    animal_div=("animal",lambda s:f.loc[s.index][f.loc[s.index,"grp"].notna() & s].pipe(lambda x:x.shape[0])) ).reset_index()
# animal_div above is fragile; recompute cleanly
adiv=f[f["animal"] & f["grp"].notna()].groupby(["IDind","wave"])["grp"].nunique().rename("animal_div").reset_index()
agg=agg.drop(columns=["animal_div"]).merge(adiv,on=["IDind","wave"],how="left")
agg["animal_div"]=agg["animal_div"].fillna(0).astype(int)
agg["animal_any"]=(agg["animal_div"]>0).astype(int)
print("DDS summary:",agg["dds"].describe()[["mean","std","min","max"]].round(2).to_dict())
print("animal_any mean:",agg["animal_any"].mean().round(3))

d=pd.read_parquet(PAN)
d=d.drop(columns=[c for c in ["dds","nfoods","animal_div","animal_any"] if c in d.columns])
d=d.merge(agg,on=["IDind","wave"],how="left")
# standardize dds for comparability
for c in ["dds","animal_div"]:
    sd=d[c].std(); d[c+"_z"]=(d[c]-d[c].mean())/sd
d.to_parquet(PAN)
print("augmented panel saved. DDS non-null:",d["dds"].notna().mean().round(3)," N with DDS:",int(d["dds"].notna().sum()))
print("DDS by wave:\n",d.groupby("wave")["dds"].mean().round(2).to_string())
