# -*- coding: utf-8 -*-
"""Full set of econometric tables from cached panels. All effects reported as
standardized (per +1 SD of the climate index) so compound vs marginal indices
are comparable. Two-way FE (pixel + year), SEs clustered at the 0.1-deg cell.
Outputs tidy CSVs (out/tables/) + readable txt + facts.json."""
import os, json, numpy as np, pandas as pd
import statsmodels.api as sm
from pathlib import Path

# ---- Path configuration ----
ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", ROOT / "outputs"))
PAN = str(OUTPUTS / "panels")
TAB = str(OUTPUTS / "tables")
os.makedirs(TAB, exist_ok=True)

COMPOUND = ["dry_hot","wet_hot","dry_cold","wet_cold"]
MARGINAL = ["TXx","TNn","PRCPTOT","CDD"]
EXTRA    = ["WSDI","SU","RX5day","SDII","DTR"]
LABELS   = {"dry_hot":"干热复合","wet_hot":"湿热复合","dry_cold":"干冷复合","wet_cold":"湿冷复合",
            "TXx":"极端高温TXx","TNn":"极端低温TNn","PRCPTOT":"年降水量","CDD":"持续干旱日数CDD",
            "WSDI":"暖期持续WSDI","SU":"夏季日数SU","RX5day":"5日最大降水","SDII":"降水强度SDII","DTR":"气温日较差"}

def zscore_in(d, cols):
    out={}
    for c in cols:
        sd=d[c].std()
        d[c+"_z"]=(d[c]-d[c].mean())/sd if sd>0 else 0.0
        out[c]=sd
    return out

def twfe(d, yvar, xz, cluster="cell", fe_year=True, region_year=False, extra_dummy=None):
    """d already has *_z columns. Pixel FE via demeaning; year (or region-year) FE via dummies."""
    d=d.dropna(subset=[yvar]+xz+[cluster,"pix","year"]).copy()
    for c in [yvar]+xz:
        d[c]=d[c]-d.groupby("pix")[c].transform("mean")
    parts=[d[xz].reset_index(drop=True)]
    if region_year:
        ry=(d["north"].astype(str)+"_"+d["year"].astype(str))
        parts.append(pd.get_dummies(ry, prefix="ry", drop_first=True).astype(float).reset_index(drop=True))
    elif fe_year:
        parts.append(pd.get_dummies(d["year"], prefix="yr", drop_first=True).astype(float).reset_index(drop=True))
    if extra_dummy is not None:
        parts.append(extra_dummy.reset_index(drop=True))
    X=pd.concat(parts,axis=1); X=sm.add_constant(X,has_constant="add")
    m=sm.OLS(d[yvar].reset_index(drop=True),X).fit(cov_type="cluster",cov_kwds={"groups":d[cluster].values})
    return m, d

def grab(m, xz):
    return pd.DataFrame({"coef":m.params[xz],"se":m.bse[xz],"t":m.tvalues[xz],"p":m.pvalues[xz]})

def stars(p):
    return "***" if p<0.01 else ("**" if p<0.05 else ("*" if p<0.1 else ""))

def load(crop): return pd.read_parquet(os.path.join(PAN,f"panel_{crop}.parquet"))

# ---------------- Table 1: descriptives ----------------
def table1():
    rows=[]
    for crop in ["maize","wheat","rice"]:
        d=load(crop)
        for v in ["start_doy","head_doy","mat_doy","gsl"]+COMPOUND+MARGINAL:
            rows.append(dict(crop=crop,var=v,mean=d[v].mean(),sd=d[v].std(),
                             p5=d[v].quantile(.05),p95=d[v].quantile(.95),N=d[v].notna().sum()))
    df=pd.DataFrame(rows)
    df.to_csv(os.path.join(TAB,"table1_descriptives.csv"),index=False,encoding="utf-8-sig")
    return df

# ---------------- Table 2: baseline ----------------
def table2():
    recs=[]; meta=[]
    for crop in ["maize","wheat","rice"]:
        d=load(crop); zscore_in(d,COMPOUND+MARGINAL)
        xz=[c+"_z" for c in MARGINAL+COMPOUND]
        for dv in ["gsl","mat_doy"]:
            m,dd=twfe(d,dv,xz)
            mc,_=twfe(d,dv,[c+"_z" for c in MARGINAL])
            inc=m.rsquared-mc.rsquared
            w=m.wald_test([f"{c}_z = 0" for c in COMPOUND],scalar=True)
            for c in MARGINAL+COMPOUND:
                recs.append(dict(crop=crop,dv=dv,block=("compound" if c in COMPOUND else "marginal"),
                                 var=c,coef=m.params[c+"_z"],se=m.bse[c+"_z"],p=m.pvalues[c+"_z"]))
            meta.append(dict(crop=crop,dv=dv,N=int(m.nobs),pixels=dd["pix"].nunique(),cells=dd["cell"].nunique(),
                             r2_full=m.rsquared,r2_marg=mc.rsquared,inc_r2=inc,
                             wald_compound_F=float(w.statistic),wald_compound_p=float(w.pvalue)))
    pd.DataFrame(recs).to_csv(os.path.join(TAB,"table2_baseline.csv"),index=False,encoding="utf-8-sig")
    pd.DataFrame(meta).to_csv(os.path.join(TAB,"table2_meta.csv"),index=False,encoding="utf-8-sig")
    return pd.DataFrame(recs),pd.DataFrame(meta)

# ---------------- Table 3: regional heterogeneity (North vs South split) ----------------
def table3():
    recs=[]
    for crop in ["maize","wheat","rice"]:
        d=load(crop)
        for region,sub in [("North",d[d.north==1]),("South",d[d.north==0])]:
            if sub["pix"].nunique()<200: continue
            sub=sub.copy(); zscore_in(sub,COMPOUND+MARGINAL)
            xz=[c+"_z" for c in MARGINAL+COMPOUND]
            m,dd=twfe(sub,"gsl",xz)
            w=m.wald_test([f"{c}_z = 0" for c in COMPOUND],scalar=True)
            for c in COMPOUND+MARGINAL:
                recs.append(dict(crop=crop,region=region,var=c,coef=m.params[c+"_z"],
                                 se=m.bse[c+"_z"],p=m.pvalues[c+"_z"],N=int(m.nobs),
                                 wald_F=float(w.statistic)))
    pd.DataFrame(recs).to_csv(os.path.join(TAB,"table3_heterogeneity.csv"),index=False,encoding="utf-8-sig")
    return pd.DataFrame(recs)

# ---------------- Table 4: adaptation over time (compound x post-2010) ----------------
def table4():
    recs=[]
    for crop in ["maize","wheat","rice"]:
        d=load(crop).copy(); d["post"]=(d["year"]>=2010).astype(int)
        zscore_in(d,COMPOUND+MARGINAL)
        base=[c+"_z" for c in MARGINAL+COMPOUND]
        for c in COMPOUND: d[c+"_z_post"]=d[c+"_z"]*d["post"]
        inter=[c+"_z_post" for c in COMPOUND]
        m,dd=twfe(d,"gsl",base+inter)  # post main effect absorbed by year FE
        for c in COMPOUND:
            recs.append(dict(crop=crop,var=c,main=m.params[c+"_z"],main_se=m.bse[c+"_z"],main_p=m.pvalues[c+"_z"],
                             x_post=m.params[c+"_z_post"],x_post_se=m.bse[c+"_z_post"],x_post_p=m.pvalues[c+"_z_post"]))
    pd.DataFrame(recs).to_csv(os.path.join(TAB,"table4_adaptation.csv"),index=False,encoding="utf-8-sig")
    return pd.DataFrame(recs)

# ---------------- Table 5: cropping-intensity turnover ----------------
def table5():
    recs=[]; meta=[]
    for name,fn,dv in [("wheat_maize","panel_turnover_wm.parquet","turnover_wm"),
                       ("double_rice","panel_turnover_rice.parquet","turnover_rice")]:
        d=pd.read_parquet(os.path.join(PAN,fn)); zscore_in(d,COMPOUND+MARGINAL)
        xz=[c+"_z" for c in MARGINAL+COMPOUND]
        m,dd=twfe(d,dv,xz)
        w=m.wald_test([f"{c}_z = 0" for c in COMPOUND],scalar=True)
        for c in MARGINAL+COMPOUND:
            recs.append(dict(system=name,dv=dv,var=c,block=("compound" if c in COMPOUND else "marginal"),
                             coef=m.params[c+"_z"],se=m.bse[c+"_z"],p=m.pvalues[c+"_z"]))
        meta.append(dict(system=name,N=int(m.nobs),pixels=dd["pix"].nunique(),mean_turnover=float(d[dv].mean()),
                         wald_compound_F=float(w.statistic),wald_compound_p=float(w.pvalue),r2=m.rsquared))
    pd.DataFrame(recs).to_csv(os.path.join(TAB,"table5_turnover.csv"),index=False,encoding="utf-8-sig")
    pd.DataFrame(meta).to_csv(os.path.join(TAB,"table5_meta.csv"),index=False,encoding="utf-8-sig")
    return pd.DataFrame(recs),pd.DataFrame(meta)

# ---------------- Table 6: robustness (maize GSL) ----------------
def table6():
    d=load("maize").copy()
    d=d.sort_values(["pix","year"])
    # lagged climate
    for c in COMPOUND+MARGINAL:
        d[c+"_lag"]=d.groupby("pix")[c].shift(1)
    zscore_in(d,COMPOUND+MARGINAL+EXTRA)
    zscore_in(d,[c+"_lag" for c in COMPOUND+MARGINAL])
    xz=[c+"_z" for c in MARGINAL+COMPOUND]
    specs={}
    m1,_=twfe(d,"gsl",xz);                         specs["(1)baseline"]=m1
    m2,_=twfe(d,"gsl",xz,cluster="cell");          # province cluster:
    # build province proxy from lon/lat grid (1-degree blocks) as coarse cluster
    d["prov_blk"]=(np.floor(d["lat"]).astype(int)*1000+np.floor(d["lon"]).astype(int))
    m2,_=twfe(d,"gsl",xz,cluster="prov_blk");      specs["(2)cluster=1deg"]=m2
    m3,_=twfe(d,"gsl",xz+[c+"_z" for c in EXTRA]); specs["(3)+extra clim"]=m3
    m4,_=twfe(d,"gsl",xz+[c+"_lag_z" for c in COMPOUND]); specs["(4)+lag compound"]=m4
    m5,_=twfe(d,"gsl",xz,region_year=True);        specs["(5)region x year FE"]=m5
    # balanced panel (pixels present all 20 yrs)
    cnt=d.groupby("pix")["year"].transform("nunique"); db=d[cnt>=20].copy()
    if len(db)>0:
        zscore_in(db,COMPOUND+MARGINAL); m6,_=twfe(db,"gsl",[c+"_z" for c in MARGINAL+COMPOUND]); specs["(6)balanced"]=m6
    recs=[]
    for spec,m in specs.items():
        for c in COMPOUND:
            recs.append(dict(spec=spec,var=c,coef=m.params[c+"_z"],se=m.bse[c+"_z"],p=m.pvalues[c+"_z"],N=int(m.nobs)))
    pd.DataFrame(recs).to_csv(os.path.join(TAB,"table6_robustness.csv"),index=False,encoding="utf-8-sig")
    return pd.DataFrame(recs)

# ---------------- facts.json (trends for intro/figures) ----------------
def facts():
    f={}
    mz=load("maize")
    yr=mz.groupby("year")["dry_hot"].mean()
    sl=np.polyfit(yr.index.values, yr.values,1)[0]
    f["dry_hot_trend_per_yr"]=float(sl); f["dry_hot_2000"]=float(yr.iloc[0]); f["dry_hot_2019"]=float(yr.iloc[-1])
    for crop in ["maize","wheat","rice"]:
        d=load(crop); g=d.groupby("year")["gsl"].mean()
        f[f"{crop}_gsl_trend_per_yr"]=float(np.polyfit(g.index.values,g.values,1)[0])
        f[f"{crop}_gsl_2000"]=float(g.iloc[0]); f[f"{crop}_gsl_2019"]=float(g.iloc[-1])
    # compound vs marginal SDs (maize)
    json.dump(f, open(os.path.join(TAB,"facts.json"),"w"), indent=2)
    return f

def main():
    out=[]
    t1=table1(); out.append("TABLE1 descriptives\n"+t1.round(2).to_string())
    t2,m2=table2(); out.append("\nTABLE2 baseline (per +1 SD)\n"+t2.round(3).to_string()+"\n"+m2.round(3).to_string())
    t3=table3(); out.append("\nTABLE3 heterogeneity North/South GSL\n"+t3.round(3).to_string())
    t4=table4(); out.append("\nTABLE4 adaptation (compound x post2010) GSL\n"+t4.round(3).to_string())
    t5,m5=table5(); out.append("\nTABLE5 turnover\n"+t5.round(3).to_string()+"\n"+m5.round(3).to_string())
    t6=table6(); out.append("\nTABLE6 robustness (maize GSL, compound coefs)\n"+t6.round(3).to_string())
    fc=facts(); out.append("\nFACTS\n"+json.dumps(fc,indent=2))
    open(os.path.join(TAB,"results_readable.txt"),"w",encoding="utf-8").write("\n".join(out))
    print("\n".join(out))
    print("\nALL TABLES WRITTEN ->", TAB)

if __name__=="__main__":
    main()
