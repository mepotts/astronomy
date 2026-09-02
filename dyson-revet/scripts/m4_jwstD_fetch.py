"""M4: list + download PUBLIC MIRI imaging products for Object_D (obs o005). Anonymous."""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pandas as pd
from astroquery.mast import Observations

ROOT = Path(r"c:/Users/matth/projects/astronomy/dyson-revet")
OUT  = ROOT/"data"/"jwst"; OUT.mkdir(parents=True, exist_ok=True)

obs = Observations.query_criteria(proposal_id="7199", dataproduct_type="image")
o = obs.to_pandas()
sel = o[o.target_name=="Object_D_background"]
print(sel[["obs_id","filters","obsid","dataRights"]].to_string())

prods = Observations.get_product_list(obs[[i for i in range(len(o)) if o.target_name.iloc[i]=="Object_D_background"]])
p = prods.to_pandas()
p.to_csv(OUT/"m4_products_D_image.csv", index=False)
print("\ntotal products:", len(p))
print(p.groupby(["productType","productSubGroupDescription","calib_level"]).size().to_string())
print("\n--- i2d ---")
i2d = p[p.productFilename.str.contains("_i2d.fits", na=False)]
print(i2d[["obs_id","productFilename","size","calib_level","productType","dataRights"]].to_string())
