# -*- coding: utf-8 -*-
"""Extract a China-region (lat 15-55N, lon 70-138E), 2000-2019 subcube
for a focused set of extreme-climate indices, cache to npz."""
import h5py, os, numpy as np
from pathlib import Path

# ---- Path configuration ----
# ROOT must point to the directory containing dataset_*_1950_2025.nc files.
# Set ERA5_DIR environment variable or edit the path below.
ROOT = Path(os.environ.get("ERA5_DIR", Path(__file__).resolve().parent.parent / "data" / "era5_raw"))
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", REPO_ROOT / "outputs"))
OUT  = str(OUTPUTS / "china_cube_2000_2019.npz")

# token -> variable name inside the nc
INDICES = {
    # compound (binary annual event mask)
    "dry_hot":  "dry_hot_events",
    "wet_hot":  "wet_hot_events",
    "dry_cold": "dry_cold_events",
    "wet_cold": "wet_cold_events",
    "warmday_night": "warmday_night_events",
    "coldday_night": "coldday_night_events",
    # heat
    "TXx": "TXx", "WSDI": "WSDI", "SU": "SU", "TR": "TR",
    # cold
    "TNn": "TNn", "FD": "FD",
    # water
    "PRCPTOT": "PRCPTOT", "CDD": "CDD", "RX5day": "RX5day", "SDII": "SDII",
    # range
    "DTR": "DTR",
}

LAT_HI, LAT_LO = 55.0, 15.0       # descending lat
LON_LO, LON_HI = 70.0, 138.0
Y0, Y1 = 2000, 2019

def main():
    # coord reference from one file
    ref = h5py.File(os.path.join(ROOT, "dataset_TXx_1950_2025.nc"), "r")
    lat = ref["latitude"][:]; lon = ref["longitude"][:]
    ref.close()
    # lat descending: find rows within [LAT_LO,LAT_HI]
    lat_mask = (lat <= LAT_HI) & (lat >= LAT_LO)
    lon_mask = (lon >= LON_LO) & (lon <= LON_HI)
    r0, r1 = np.where(lat_mask)[0][[0, -1]]
    c0, c1 = np.where(lon_mask)[0][[0, -1]]
    lat_sub = lat[r0:r1+1]; lon_sub = lon[c0:c1+1]
    print(f"lat rows {r0}:{r1+1} ({len(lat_sub)}) {lat_sub[0]:.1f}->{lat_sub[-1]:.1f}")
    print(f"lon cols {c0}:{c1+1} ({len(lon_sub)}) {lon_sub[0]:.1f}->{lon_sub[-1]:.1f}")

    store = {"lat": lat_sub.astype("float32"), "lon": lon_sub.astype("float32")}
    years_target = np.arange(Y0, Y1 + 1)
    store["years"] = years_target.astype("int32")

    for tok, var in INDICES.items():
        p = os.path.join(ROOT, f"dataset_{tok}_1950_2025.nc")
        if not os.path.exists(p):
            # some tokens have _nc suffix in filename
            alt = os.path.join(ROOT, f"dataset_{tok}_nc_1950_2025.nc")
            p = alt if os.path.exists(alt) else p
        f = h5py.File(p, "r")
        yrs = f["year"][:]
        yi = np.array([np.where(yrs == y)[0][0] for y in years_target])
        ys, ye = yi.min(), yi.max() + 1
        arr = f[var][ys:ye, r0:r1+1, c0:c1+1].astype("float32")
        # reorder to exactly years_target (contiguous here, but be safe)
        sel = yi - ys
        arr = arr[sel]
        f.close()
        store[tok] = arr
        finite = np.isfinite(arr)
        vmin = float(np.nanmin(arr)) if finite.any() else float("nan")
        vmax = float(np.nanmax(arr)) if finite.any() else float("nan")
        vmean = float(np.nanmean(arr)) if finite.any() else float("nan")
        print(f"{tok:14s} shape {arr.shape} min {vmin:.2f} max {vmax:.2f} mean {vmean:.3f}")

    np.savez_compressed(OUT, **store)
    print("SAVED ->", OUT, "size MB", os.path.getsize(OUT)/1e6)

if __name__ == "__main__":
    main()
