"""M4: query MAST anonymously for JWST GO 7199 (Hephaistos IV). No login, no token."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pandas as pd
from astroquery.mast import Observations

ROOT = Path(r"c:/Users/matth/projects/astronomy/dyson-revet")
OUT  = ROOT / "data" / "jwst"
OUT.mkdir(parents=True, exist_ok=True)

# explicitly anonymous
try:
    print("logged in?", Observations.is_token_valid if hasattr(Observations,'is_token_valid') else 'n/a')
except Exception as e:
    print("tokcheck", e)

obs = Observations.query_criteria(proposal_id="7199")
print("N obs =", len(obs))
df = obs.to_pandas()
cols = ["obsid","obs_id","obs_collection","instrument_name","filters","target_name",
        "s_ra","s_dec","t_exptime","dataRights","t_obs_release","calib_level","dataproduct_type",
        "proposal_pi","t_min","t_max","obs_title","project","intentType","provenance_name"]
cols = [c for c in cols if c in df.columns]
df[cols].to_csv(OUT/"m4_obs_7199.csv", index=False)
pd.set_option("display.width", 400); pd.set_option("display.max_columns", 50)
print(df[["obs_id","instrument_name","filters","target_name","t_exptime","dataRights","t_obs_release","calib_level","dataproduct_type"]].to_string())
print("\nPI:", df["proposal_pi"].unique(), "\nTitle:", df["obs_title"].unique())
