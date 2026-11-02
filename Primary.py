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