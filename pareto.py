import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # lets it save a chart file without opening a window
import matplotlib.pyplot as plt
import os
os.makedirs("reports/figures", exist_ok=True)

# opening the database and pulling the pciking data 
con = sqlite3.connect("db/supply_chain.db")
df = pd.read_sql("SELECT sku_id, units_sold FROM demand_history", con)
con.close()

# Adding up total picks for each SKU

picks = (df.groupby("sku_id")["units_sold"].sum()
         .sort_values(ascending=False)
         .reset_index())

picks["cum_pct"]= picks["units_sold"].cumsum() / picks["units_sold"].sum() * 100

# What this does is that marks every SKUs until under the 80% line and 
# counts them and answers the fact that what share of SKUs do I need to cover 80% of picks
pct_skus_for_80= (picks["cum_pct"] < 80).sum() / len(picks) * 100
print(f"{pct_skus_for_80:.1f}% of SKUs make up the 80% of picks")

print (picks.head(10))

picks["rank"] = range(1, len(picks) + 1)   # label SKUs 1,2,3... in speed order (x-axis)

fig, ax1 = plt.subplots(figsize=(10, 5))                    # create a chart canvas, 10x5 inches  
ax1.bar(picks["rank"], picks["units_sold"], width=1.0, color="#4C78A8") # create a chart canvas, 10x5 inches
ax1.set_xlabel("SKU rank (fastest-moving first)") # label the x-axis
ax1.set_ylabel("Picks")                           # label the left y-axis

ax2 = ax1.twinx()                            # a second y-axis on the right
ax2.plot(picks["rank"], picks["cum_pct"], color="#E45756", linewidth=2) # red cumulative line
ax2.axhline(80, color="gray", linestyle="--")   # the 80% reference line
ax2.set_ylabel("Cumulative % of picks")         # label the right y-axis   

plt.title("Pareto of SKU pick frequency (80/20)")
fig.tight_layout()
fig.savefig("reports/figures/pareto_picks.png", dpi=150)
print("Chart saved to reports/figures/pareto_picks.png")