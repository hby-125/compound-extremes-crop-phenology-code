# -*- coding: utf-8 -*-
import h5py, glob, os, numpy as np
from pathlib import Path

# Set ERA5_DIR or edit the path below
root = os.environ.get("ERA5_DIR", str(Path(__file__).resolve().parent.parent / "data" / "era5_raw"))
files = sorted(glob.glob(os.path.join(root, "dataset_*.nc")))
print("n files:", len(files))
for p in files:
    name = os.path.basename(p)
    try:
        f = h5py.File(p, "r")
    except Exception as e:
        print(name, "OPEN-ERR", repr(e)[:80]); continue
    dvars = [k for k in f.keys() if isinstance(f[k], h5py.Dataset) and f[k].ndim == 3]
    coords = [k for k in f.keys() if isinstance(f[k], h5py.Dataset) and f[k].ndim == 1]
    info = []
    for v in dvars:
        ds = f[v]
        attrs = {a: (ds.attrs[a].decode() if isinstance(ds.attrs[a], bytes) else str(ds.attrs[a]))
                 for a in ds.attrs if a in ("units", "long_name", "standard_name", "_FillValue")}
        info.append((v, ds.shape, ds.dtype.str, attrs))
    print("==", name)
    print("   coords:", coords, "| 3D vars:", info)
    f.close()
