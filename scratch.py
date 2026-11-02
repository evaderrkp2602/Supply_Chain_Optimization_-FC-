import numpy as np
import pandas as pd
rng = np.random.default_rng(42)

N_SKUS = 500
CATEGORIES = ["Raw", "Component", "Finished"]

# build each column
sku_ids       = np.arange(1, N_SKUS + 1)
names         = [f"SKU-{i:04d}" for i in range(1, N_SKUS + 1)]
categories    = rng.choice(CATEGORIES, N_SKUS)
unit_costs    = rng.uniform(2, 200, N_SKUS).round(2)
supplier_ids  = rng.choice([1, 2, 3], N_SKUS, p=[0.50, 0.35, 0.15])
unit_prices   = (unit_costs * rng.uniform(1.3, 2.2, N_SKUS)).round(2)

# snap them together into one table
products = pd.DataFrame({
    "sku_id":      sku_ids,
    "name":        names,
    "category":    categories,
    "unit_cost":   unit_costs,
    "supplier_id": supplier_ids,
    "unit_price":  unit_prices,
})

print(products.head(10))                    # first 10 rows
print("\nProducts per supplier:")
print(products["supplier_id"].value_counts())

N_Weeks = 6 
DCS = [3,4,5]
dc_split = [0.40, 0.35, 0.25]

demand_rows = []

for sku in [1,2,3]:
    base = rng.uniform(20,300)
    season_amp = rng.uniform(0.1, 0.4) * base

    for w in range(N_Weeks):
        season = season_amp * np.sin(2 * np.pi * w / 52)
        on_promo = 1 if rng.random() < 0.05 else 0
        total = base + season + on_promo * base * 0.8 + rng.normal(0, base * 0.2)#Promo & Random Jitter Respectifully
        total = max(0, total)

        for dc, share in zip(DCS, dc_split):
            units = round(total * share)
            demand_rows.append ([w, sku, dc, units, on_promo])

demand = pd.DataFrame(demand_rows,
columns=["week", "sku_id", "loc_id", "units_sold", "on_promo"])

print(demand.head(12))
print("\nTotal rows:", len(demand))
