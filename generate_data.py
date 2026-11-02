import os, sqlite3
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N_SKUS, N_WEEKS = 500, 104
CATEGORIES = ["Raw", "Component", "Finished"]
week_dates = pd.date_range("2024-01-01", periods=N_WEEKS, freq="W-MON").strftime("%Y-%m-%d")
os.makedirs("data/processed", exist_ok=True)
os.makedirs("db", exist_ok=True)

locations = pd.DataFrame({
    "loc_id":[1,2,3,4,5],
    "name":["Plant-A","Plant-B","DC-East","DC-Central","DC-West"],
    "type":["Plant","Plant","DC","DC","DC"],
    "region":["Midwest","South","East","Central","West"],
    "holding_cost_rate":[0.0,0.0,0.25,0.25,0.30],
    "capacity_units":[0,0,40000,35000,30000]})
DCS, dc_split = [3,4,5], [0.40,0.35,0.25]

suppliers = pd.DataFrame({
    "supplier_id":[1,2,3],
    "name":["Rel-Corp","MidCo","SlowVendor"],
    "region":["Domestic","Domestic","Overseas"],
    "avg_lead_time_days":[7,14,30],
    "lead_time_std":[1,3,10],
    "reliability":[0.98,0.95,0.85]})

sku_ids = np.arange(1, N_SKUS+1)
products = pd.DataFrame({
    "sku_id":sku_ids,
    "name":[f"SKU-{i:04d}" for i in range(1,N_SKUS+1)],
    "category":rng.choice(CATEGORIES,N_SKUS),
    "unit_cost":rng.uniform(2,200,N_SKUS).round(2),
    "supplier_id":rng.choice([1,2,3],N_SKUS,p=[0.50,0.35,0.15])})
products["unit_price"]=(products["unit_cost"]*rng.uniform(1.3,2.2,N_SKUS)).round(2)

demand_rows=[]
for sku in sku_ids:
    base=rng.lognormal(3.0,1.5)
    erratic=rng.random()<0.15
    noise=base*(0.6 if erratic else 0.2)
    amp=rng.uniform(0.1,0.4)*base
    for w in range(N_WEEKS):
        season=amp*np.sin(2*np.pi*w/52)
        promo=1 if rng.random()<0.05 else 0
        total=max(0,base+season+promo*base*0.8+rng.normal(0,noise))
        for dc,share in zip(DCS,dc_split):
            demand_rows.append([week_dates[w],int(sku),dc,max(0,round(total*share)),promo])
demand_history=pd.DataFrame(demand_rows,columns=["date","sku_id","loc_id","units_sold","on_promo"])

rev=demand_history.groupby("sku_id")["units_sold"].sum().reset_index()
rev=rev.merge(products[["sku_id","unit_price"]],on="sku_id")
rev["revenue"]=rev["units_sold"]*rev["unit_price"]
rev=rev.sort_values("revenue",ascending=False)
rev["cum_pct"]=rev["revenue"].cumsum()/rev["revenue"].sum()
rev["abc_class"]=np.where(rev["cum_pct"]<=0.80,"A",np.where(rev["cum_pct"]<=0.95,"B","C"))
products=products.merge(rev[["sku_id","abc_class"]],on="sku_id")

lanes=pd.DataFrame([[o,d,round(rng.uniform(3,10),2),int(rng.integers(2,8))]
    for o in [1,2] for d in DCS],
    columns=["origin_loc_id","dest_loc_id","cost_per_unit","transit_days"])

avg_wk=demand_history.groupby(["sku_id","loc_id"])["units_sold"].mean().to_dict()
inv_rows=[]
for (sku,dc),avg in avg_wk.items():
    oh=max(0,avg*rng.uniform(2,6))
    for wd in week_dates[::4]:
        oh=max(0,oh+rng.normal(0,avg*0.3))
        inv_rows.append([wd,sku,dc,round(oh),round(max(0,avg*rng.uniform(0,2)))])
inventory_snapshots=pd.DataFrame(inv_rows,columns=["date","sku_id","loc_id","on_hand","on_order"])

tables={"products":products,"suppliers":suppliers,"locations":locations,
    "demand_history":demand_history,"lanes":lanes,"inventory_snapshots":inventory_snapshots}
con=sqlite3.connect("db/supply_chain.db")
for name,df in tables.items():
    df.to_csv(f"data/processed/{name}.csv",index=False)
    df.to_sql(name,con,if_exists="replace",index=False)
con.close()

print("Done. Row counts:")
for name,df in tables.items():
    print(f"  {name:22s} {len(df):>8,} rows")
print("\nABC split:\n", products["abc_class"].value_counts())
print("\nSaved -> data/processed/*.csv and db/supply_chain.db")

