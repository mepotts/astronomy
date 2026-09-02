import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pandas as pd
from astroquery.mast import Observations
ROOT = Path(r"c:/Users/matth/projects/astronomy/dyson-revet")
OUT  = ROOT/"data"/"jwst"
obs = Observations.query_criteria(proposal_id="7199", dataproduct_type="image")
o = obs.to_pandas()
idx = [i for i in range(len(o)) if o.target_name.iloc[i]=="Object_D_background"]
prods = Observations.get_product_list(obs[idx])
p = prods.to_pandas()
mask = p.productFilename.str.match(r"jw07199-o005_t007_miri_f\d+w_i2d\.fits") | \
       p.productFilename.str.match(r"jw07199-o005_t007_miri_f\d+w_cat\.ecsv") | \
       p.productFilename.str.match(r"jw07199-o005_t007_miri_f\d+w_segm\.fits")
sel = prods[list(mask.values)]
print("selected:", list(p.productFilename[mask.values]))
m = Observations.download_products(sel, download_dir=str(OUT), flat=True)
print(m)
