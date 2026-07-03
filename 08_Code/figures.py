# -*- coding: utf-8 -*-
"""Paper figures (English labels for font safety). Reads cached panels + tidy tables."""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ---- Path configuration ----
ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", ROOT / "outputs"))
PAN = str(OUTPUTS / "panels")
TAB = str(OUTPUTS / "tables")
FIG = str(OUTPUTS / "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
COMP=["dry_hot","wet_hot","dry_cold","wet_cold"]; MARG=["TXx","TNn","PRCPTOT","CDD"]
def load(c): return pd.read_parquet(os.path.join(PAN,f"panel_{c}.parquet"))

# ---- Fig 1: compound-extreme trend + spatial distribution ----
def fig1():
    mz=load("maize")
    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    ax=axes[0]
    for v,co in zip(COMP,["#d62728","#ff7f0e","#1f77b4","#2ca02c"]):
        g=mz.groupby("year")[v].mean()
        ax.plot(g.index,g.values,marker="o",ms=3,label=v,color=co)
    ax.set_xlabel("Year"); ax.set_ylabel("Compound-event days per year (cropland mean)")
    ax.set_title("(a) Trend of compound climate extremes, 2000-2019")
    ax.legend(frameon=False,fontsize=8,ncol=2)
    ax2=axes[1]
    s=mz.groupby(["lon","lat"])["dry_hot"].mean().reset_index()
    sc=ax2.scatter(s["lon"],s["lat"],c=s["dry_hot"],s=2,cmap="YlOrRd",vmin=5,vmax=45)
    ax2.set_xlabel("Longitude"); ax2.set_ylabel("Latitude")
    ax2.set_title("(b) Mean dry-hot compound days over maize pixels")
    plt.colorbar(sc,ax=ax2,label="days/yr",shrink=0.85)
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig1_compound_trend_map.png"),dpi=300,bbox_inches="tight")
    print("fig1 done")

# ---- Fig 2: baseline coefficient plot (GSL) ----
def fig2():
    df=pd.read_csv(os.path.join(TAB,"table2_baseline.csv"),encoding="utf-8-sig")
    df=df[df.dv=="gsl"]
    order=MARG+COMP; crops=["maize","wheat","rice"]
    df["yo"]=df["var"].map({v:i for i,v in enumerate(order)})
    fig,axes=plt.subplots(1,3,figsize=(12,4.3),sharex=True)
    for ax,crop in zip(axes,crops):
        d=df[df.crop==crop].sort_values("yo"); y=np.arange(len(order))
        colors=["#1f77b4" if v in MARG else "#d62728" for v in d["var"]]
        ax.errorbar(d["coef"],y,xerr=1.96*d["se"],fmt="o",color="black",ecolor="gray",capsize=2,zorder=3)
        ax.scatter(d["coef"],y,c=colors,s=55,zorder=4)
        ax.axvline(0,color="k",lw=0.8,ls="--")
        ax.axhspan(len(MARG)-0.5,len(order)-0.5,color="#d62728",alpha=0.06)
        ax.set_yticks(y); ax.set_yticklabels(order); ax.set_title(crop.capitalize())
        ax.set_xlabel("Days of growing season per +1 SD")
    axes[0].set_ylabel("Climate index")
    fig.legend(handles=[mpatches.Patch(color="#1f77b4",label="Marginal index"),
                        mpatches.Patch(color="#d62728",label="Compound extreme")],
               loc="lower center",ncol=2,frameon=False,bbox_to_anchor=(0.5,-0.04))
    fig.suptitle("Effect of extreme-climate indices on growing-season length (two-way FE)",y=1.0)
    fig.tight_layout(rect=[0,0.04,1,1]); fig.savefig(os.path.join(FIG,"fig2_coef_gsl.png"),dpi=300,bbox_inches="tight")
    print("fig2 done")

# ---- Fig 3: regional heterogeneity (North vs South) ----
def fig3():
    df=pd.read_csv(os.path.join(TAB,"table3_heterogeneity.csv"),encoding="utf-8-sig")
    df=df[df["var"].isin(COMP)]
    crops=["maize","wheat","rice"]
    fig,axes=plt.subplots(1,3,figsize=(12,4),sharey=True)
    x=np.arange(len(COMP)); w=0.38
    for ax,crop in zip(axes,crops):
        for i,(reg,co) in enumerate([("North","#4477aa"),("South","#cc6677")]):
            d=df[(df.crop==crop)&(df.region==reg)].set_index("var").reindex(COMP)
            ax.bar(x+(i-0.5)*w,d["coef"],w,yerr=1.96*d["se"],capsize=2,label=reg,color=co)
        ax.axhline(0,color="k",lw=0.8); ax.set_xticks(x); ax.set_xticklabels(COMP,rotation=20)
        ax.set_title(crop.capitalize()); ax.set_xlabel("")
    axes[0].set_ylabel("Effect on GSL (days per +1 SD)"); axes[0].legend(frameon=False)
    fig.suptitle("Regional heterogeneity: compound-extreme effects on GSL, North (lat>=33) vs South",y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig3_heterogeneity.png"),dpi=300,bbox_inches="tight")
    print("fig3 done")

# ---- Fig 4: adaptation, pre vs post 2010 (dry_hot & wet_hot) ----
def fig4():
    df=pd.read_csv(os.path.join(TAB,"table4_adaptation.csv"),encoding="utf-8-sig")
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,var in zip(axes,["dry_hot","wet_hot"]):
        d=df[df["var"]==var].set_index("crop").reindex(["maize","wheat","rice"])
        pre=d["main"]; post=d["main"]+d["x_post"]
        x=np.arange(3); w=0.38
        ax.bar(x-w/2,pre,w,label="2000-2009",color="#88ccee")
        ax.bar(x+w/2,post,w,label="2010-2019",color="#cc6677")
        ax.axhline(0,color="k",lw=0.8); ax.set_xticks(x); ax.set_xticklabels(["maize","wheat","rice"])
        ax.set_title(var); ax.set_xlabel("")
    axes[0].set_ylabel("Effect on GSL (days per +1 SD)"); axes[0].legend(frameon=False)
    fig.suptitle("Change in crop-phenology sensitivity to compound extremes over time",y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig4_adaptation.png"),dpi=300,bbox_inches="tight")
    print("fig4 done")

if __name__=="__main__":
    fig1(); fig2(); fig3(); fig4()
    print("ALL FIGS ->",FIG)
